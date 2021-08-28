import argparse
import cv2
import torch
torch.cuda.set_device(1)
from model import SCNN
from model_ENET_SAD import ENet_SAD
from utils.prob2lines import getLane
from utils.transforms import *
import numpy as np

import time
from multiprocessing import Process, JoinableQueue, SimpleQueue
from threading import Lock

img_size = (800, 288)
#net = SCNN(input_size=(800, 288), pretrained=False)
net = ENet_SAD(img_size, sad=False)
# CULane mean, std
mean=(0.3598, 0.3653, 0.3662)
std=(0.2573, 0.2663, 0.2756)
# Imagenet mean, std
# mean=(0.485, 0.456, 0.406)
# std=(0.229, 0.224, 0.225)
transform_img = Resize(img_size)
transform_to_net = Compose(ToTensor(), Normalize(mean=mean, std=std))

pipeline = False

prepoints = 1 # this for count lane...

def parse_args():
    parser = argparse.ArgumentParser()
    #parser.add_argument("--video_path", '-i', type=str, default="demo/ioniq.webm", help="Path to demo video")
    parser.add_argument("--weight_path", '-w', type=str, default="experiments/exp1_culane/exp1_best.pth", help="Path to model weights")
    parser.add_argument("--video_path", '-i', type=str, default="/home/dgist/Desktop/data/원내주행영상/낮/0626/E16todorm.webm", help="Path to demo video")
    parser.add_argument("--camera", '-c', type=str, default=False, help="using camera or not")
    parser.add_argument("--visualize", '-v', action="store_true", default=True, help="Visualize the result")
    args = parser.parse_args()
    return args


def network(net, img):
    seg_pred, exist_pred = net(img.cuda())[:2]
    seg_pred = seg_pred.detach().cpu()
    exist_pred = exist_pred.detach().cpu()
    return seg_pred, exist_pred


def visualize(img, seg_pred, exist_pred):
    # img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    lane_img = np.zeros_like(img)
    color = np.array([[255, 125, 0], [0, 255, 0], [0, 0, 255], [0, 255, 255]], dtype='uint8')
    coord_mask = np.argmax(seg_pred, axis=0)
    for i in range(0, 4):
        if exist_pred[0, i] > 0.5:
            lane_img[coord_mask == (i + 1)] = color[i]
    img = cv2.addWeighted(src1=lane_img, alpha=0.8, src2=img, beta=1., gamma=0.)
    return img


def pre_processor(arg):
    img_queue, video_path = arg
    cap = cv2.VideoCapture(video_path)
    while cap.isOpened():
        if img_queue.empty():
            ret, frame = cap.read()
            if ret:
                #frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
                frame = transform_img({'img': frame})['img']
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                x = transform_to_net({'img': img})['img']
                x.unsqueeze_(0)

                img_queue.put(x)
                img_queue.join()
            else:
                break


def post_processor(arg):
    img_queue, arg_visualize = arg

    while True:
        if not img_queue.empty():
            x, seg_pred, exist_pred = img_queue.get()
            seg_pred = seg_pred.numpy()[0]
            exist_pred = exist_pred.numpy()

            exist = [1 if exist_pred[0, i] > 0.5 else 0 for i in range(4)]

            print(exist)
            for i in getLane.prob2lines_CULane(seg_pred, exist):
                print(i)

            if arg_visualize:
                frame = x.squeeze().permute(1, 2, 0).numpy()
                img = visualize(frame, seg_pred, exist_pred)
                cv2.imshow('input_video', frame)
                cv2.imshow("output_video", img)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        else:
            pass


# when change in the number of lanes, no recognition, not enough sample points, make re-evalution sign
def re_eval_sign(points):
    global prepoints
    if prepoints == 0:
        return False
    counter = 0
    for i in range(4):
        if points[i] != [None]:
            counter +=1
    if counter != prepoints:
        prepoints = counter
        return True
    else:
        prepoints = counter
        return False
        

def centerline_visualize(img, seg_pred, exist_pred):
    cv2.imshow("img", img)
    mask_img = np.zeros((6,6))
    coord_mask = np.argmax(seg_pred, axis=0)
    color_choice = []
    # try:
    for i in range(0, 4):
        voting_list = []
        if exist_pred[0][i] > 0.5:
            # mask_img[coord_mask == (i+1)] = img[coord_mask == (i+1)]
            y_list, x_list = np.where(coord_mask == i+1)
            if len(x_list) != 0:
                for j in range(7):
                    idx = random.randint(0, len(x_list)-1)
                    x, y = x_list[idx], y_list[idx]
                    mask_img = img[x-3:x+3, y-3:y+3]
                    # print("white_num: ", detect_white(mask_img))
                    # print("yellow_num: ", detect_yellow(mask_img))
                    voting_list.append(decision(detect_white(mask_img), detect_yellow(mask_img)))
                    # cv2.circle(img, (x,y), 10,(255,0,0) , -1)
                    # cv2.imshow("cir",img)
                color_choice.insert(i, voting(voting_list))
            else:
                color_choice.insert(i, "N")
        else:
            color_choice.insert(i, "N")
    return color_choice

def detect_white(mask_img):
    # White-ish areas in image
    # H value can be arbitrary, thus within [0 ... 360] (OpenCV: [0 ... 180])
    # L value must be relatively high (we want high brightness), e.g. within [0.7 ... 1.0] (OpenCV: [0 ... 255])
    # S value must be relatively low (we want low saturation), e.g. within [0.0 ... 0.3] (OpenCV: [0 ... 255])
    white_lower = np.array([np.round(  0 / 2), np.round(0.65 * 255), np.round(0.00 * 255)])
    white_upper = np.array([np.round(360 / 2), np.round(1.00 * 255), np.round(0.30 * 255)])
    try:
        white_mask = cv2.inRange(mask_img, white_lower, white_upper)
        # cv2.imshow("white", white_mask)
        return len(np.where(white_mask!= 0)[0])
    except:
        return 0

def detect_yellow(mask_img):
    # Yellow-ish areas in image
    # H value must be appropriate (see HSL color space), e.g. within [40 ... 60]
    # L value can be arbitrary (we want everything between bright and dark yellow), e.g. within [0.0 ... 1.0]
    # S value must be above some threshold (we want at least some saturation), e.g. within [0.35 ... 1.0]
    yellow_lower = np.array([np.round( 20 / 2), np.round(0.00 * 255), np.round(0.35 * 255)])
    yellow_upper = np.array([np.round( 60 / 2), np.round(1.00 * 255), np.round(1.00 * 255)])
    try:
        yellow_mask = cv2.inRange(mask_img, yellow_lower, yellow_upper)
        return len(np.where(yellow_mask!= 0)[0])
    except:
        return 0


def decision(white, yellow):
    if white == 0 and yellow == 0:
        return "N"
    elif white > yellow:
        return "w"
    elif white <= yellow:
            return "y"


def voting(voting_list):
    if voting_list.count("y") != 0:
        if voting_list.count("w") > 2*voting_list.count("y"):
            return "w"
        return "y"
    elif voting_list.count("w") != 0:
        return "w"
    else:
        return "N"

def my_lane(color_list):
    try:
        idx = color_list.index("y")
        if idx == 0:
            try:
                if color_list[1:].index("y") == 0:
                    try:
                        if color_list[2:].index("y") == 0:
                            return -1
                        else:
                            return -1
                    except:
                        return 1
                else:
                    return -1
            except:
                return 2 
        elif idx == 1:
            try:
                if color_list[2:].index("y") == 0:
                    return -1
                else:
                    return -1
            except:
                return 1

        else:
            return -1
    except:
        try:
            if color_list.count("w") !=0:
                return 1
            else:
                pass
        except:
            pass

def draw_my_lane(img, num_of_my_lane):
    img = cv2.rectangle(img, (730,2), (795, 15), (255,255,255), -1)
    img = cv2.putText(img, "lane: "+ str(num_of_my_lane), (730, 10), 0, 0.4,(0,0,0))
    return img


def for_degree(x1,x2,y1,y2):
    return (np.arctan2(x1-x2, y1-y2) * 180) / np.pi

def using_degree(x_list, y_list, idx,img):
    degree = [[-85, -75], [-70, -50], [50, 70], [75, 85]]
    #degree = [[-90, -75], [-75, -50], [50, 75], [75, 90]]
    #print(degree[idx][1])
    start_points = [[0, 220], [180, 286], [580,287], [798, 240]]
    #print(degree[idx][1])
    x1, y1 = start_points[idx][0], start_points[idx][1]
    x_new = [x_list[-1]]
    y_new = [y_list[-1]]
    #print("::::pts::::",line)
    for pts in range(20, len(x_list)):
        if 50 <int(x_list[pts])<750 and 160 < int(y_list[pts]) < 280:
            x2, y2 = int(x_list[pts]), int(y_list[pts])
            # cv2.circle(img, (x2,y2), 10, (255,0,0), -1)
        
            # cv2.putText(img, str(idx), (x2, y2),cv2.FONT_HERSHEY_COMPLEX,0.4,(255,255,255),1)
            #slope_degree = for_degree(x1,x2, y1, y2)
            slope_degree = (np.arctan2(x1-x2, y1-y2) * 180) / np.pi
            if degree[idx][0] < (slope_degree) < degree[idx][1]:
                x_new.append(x2)
                y_new.append(y2)
    return x_new, y_new



def draw_polynomial_regression_lane(x_list, y_list, img, color_choice):
    lane_img = np.zeros_like(img)  
    try:
        # polynomial regression
        fp1 = np.polyfit(np.array(x_list), np.array(y_list) , 3)
        f1 = np.poly1d(fp1)
        y_list = np.polyval(f1, x_list)
        draw_poly = np.array([list(zip(x_list, y_list))], np.int32)
        if color_choice == "N":
            lane_img=cv2.polylines(lane_img, np.asarray(draw_poly), False, (0, 255, 0), 3)
        if color_choice == "w":
            lane_img=cv2.polylines(lane_img, np.asarray(draw_poly), False, (255, 255, 255), 3)
        if color_choice == "y":
            lane_img=cv2.polylines(lane_img, np.asarray(draw_poly), False, (255, 255, 0), 3)
        if color_choice == "center":
            lane_img=cv2.polylines(lane_img, np.asarray(draw_poly), False, (139, 0, 255), 3)     
        #lane_img=cv2.polylines(lane_img, np.asarray(draw_poly), False, draw_color, 3)
    except:
        pass
    img = cv2.addWeighted(src1=lane_img, alpha=0.8, src2=img, beta=1., gamma=0.)
    return lane_img, img


def affine_trasform(lane_img):
    # coordinate lu -> ld -> ru -> rd
    pts1 = np.float32([[265,165],[0, 215],[500,165],[798, 240]])

    # pts2 is points to move from pts1.
    pts2 = np.float32([[0,0],[0,300],[300,0],[300,300]])
    M = cv2.getPerspectiveTransform(pts1, pts2)

    dst = cv2.warpPerspective(lane_img, M, (300,300))
    dst = cv2.resize(dst, dsize=(70,70))
    return dst


def overwrap(lane_img, img):
    rows, cols, channels = lane_img.shape
    roi = img[10:rows+10, 10:cols+10]

    img2gray = cv2.cvtColor(lane_img, cv2.COLOR_RGB2GRAY)
    ret, mask = cv2.threshold(img2gray, 10, 255, cv2.THRESH_BINARY)
    mask_inv = cv2.bitwise_not(mask)

    img1_bg = cv2.bitwise_and(roi, roi, mask=mask_inv)

    img2_fg = cv2.bitwise_and(lane_img, lane_img, mask=mask)

    dst = cv2.add(img1_bg, img2_fg)
    img[10:rows+10, 10:cols+10] = dst

    return img

def draw_forward(x_list, y_list, i, img):
    lane_img = np.zeros_like(img) 
    x_left = []
    x_right = [] 
    y_center = []
    if i ==2:
        x_left = x_list
        y_left = y_list
    elif i ==3:
        x_right = x_list
        y_right = y_list
    if len(x_left)>=3 and len(x_right) >=3:
        x_center = [(x+y)/2 for x,y in zip(x_left, x_right)]
        y_center = [(x+y)/2 for x,y in zip(y_left, y_right)]
        x_mid = x_center[-3]
        y_mid = y_center[-3]
        x_last = x_center[-1]
        y_last = y_center[-1]
        steering = for_degree(x_mid, x_last, y_mid, y_last)
        print("steering: ", steering)
        lane_img, img = draw_polynomial_regression_lane(x_center, y_center, img, "center")


def main():
    args = parse_args()
    video_path = args.video_path
    weight_path = args.weight_path

   # -----------------------
    color_choice = ["N", "N", "N", "N"]
    num_of_my_lane = 0
    frame_100 = 0
    global prepoints
   # ---------------------


    if pipeline:
        input_queue = JoinableQueue()
        pre_process = Process(target=pre_processor, args=((input_queue, video_path),))
        pre_process.start()

        output_queue = SimpleQueue()
        post_process = Process(target=post_processor, args=((output_queue, args.visualize),))
        post_process.start()
    elif args.camera:
        cap = cv2.VideoCapture(0)
    else:
        cap = cv2.VideoCapture(video_path)

    save_dict = torch.load(weight_path, map_location='cpu')
    #save_dict['net']['fc.0.weight'] = save_dict['net']['fc.0.weight'].view(128,4400)
    #print(save_dict['net']['fc.0.weight'].view(128,4400))
    net.load_state_dict(save_dict['net'])

    net.eval()
    net.cuda()

    while True:
        if pipeline:
            loop_start = time.time()
            x = input_queue.get()
            input_queue.task_done()

            gpu_start = time.time()
            seg_pred, exist_pred = network(net, x)
            gpu_end = time.time()

            output_queue.put((x, seg_pred, exist_pred))

            loop_end = time.time()

        else:
            if not cap.isOpened():
                break

            ret, frame = cap.read()
            frame_100 += 1

            if ret:
                loop_start = time.time()
                #frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
                frame = transform_img({'img': frame})['img']
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                x = transform_to_net({'img': img})['img']
                x.unsqueeze_(0)
                gpu_start = time.time()
                seg_pred, exist_pred = network(net, x)
                gpu_end = time.time()

                seg_pred = seg_pred.numpy()[0]
                exist_pred = exist_pred.numpy()

                exist = [1 if exist_pred[0, i] > 0.5 else 0 for i in range(4)]

                # for i in getLane.prob2lines_CULane(seg_pred, exist):
                    # print(i)

                points = getLane.prob2lines_CULane_make(seg_pred, exist, pts=30)
                if re_eval_sign(points) == True or frame_100 == 50:
                    frame_100 = 0
                    hls = cv2.cvtColor(img, cv2.COLOR_RGB2HLS)
                    color_choice = centerline_visualize(hls, seg_pred, exist_pred)
                    print(color_choice)
                    num_of_my_lane = my_lane(color_choice)
                img = draw_my_lane(img, num_of_my_lane)


                coord_mask = np.argmax(seg_pred, axis=0)
                for i in range(0, 4):
                    voting_list = []
                    if exist_pred[0][i] > 0.5:
                        # mask_img[coord_mask == (i+1)] = img[coord_mask == (i+1)]
                        y_list, x_list = np.where(coord_mask == i+1)
                        if len(x_list) >=3:
                            x_list1, y_list1 = using_degree(x_list, y_list, i, img)
                            lane_img, img = draw_polynomial_regression_lane(x_list, y_list, img, color_choice[i])
                            lane_img = affine_trasform(lane_img)
                            img = overwrap(lane_img, img)
 

                # lane_img = affine_trasform(lane_img)
                # img = overwrap(lane_img, img)
                # lane_img, img = draw_forward(points, img)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                loop_end = time.time()

                if args.visualize:
                    # img = visualize(img, seg_pred, exist_pred)
                    cv2.imshow('input_video', frame)
                    cv2.imshow("output_video", img)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                break

        # print("gpu_runtime:", gpu_end - gpu_start, "FPS:", int(1 / (gpu_end - gpu_start)))
        # print("total_runtime:", loop_end - loop_start, "FPS:", int(1 / (loop_end - loop_start)))

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

