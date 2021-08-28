/*
 * Copyright (C) 2019 by AutoSense Organization. All rights reserved.
 * Gary Chan <chenshj35@mail2.sysu.edu.cn>
 */

#include <pcl_conversions/pcl_conversions.h>  // pcl::fromROSMsg
#include <ros/ros.h>
#include <sensor_msgs/PointCloud2.h>
#include <std_msgs/Header.h>
#include "std_msgs/Int16.h"
#include <visualization_msgs/MarkerArray.h>
#include <memory>

#include "common/color.hpp"
#include "common/parameter.hpp"  // common::getSegmenterParams
#include "common/publisher.hpp"  // common::publishCloud
#include "common/time.hpp"       // common::Clock
#include "common/types/type.h"   // PointICloudPtr
#include "object_builders/object_builder_manager.hpp"
#include "roi_filters/roi.hpp"               // roi::applyROIFilter
#include "segmenters/segmenter_manager.hpp"  // segmenter::createGroundSegmenter

using namespace autosense;  // NOLINT

const std::string param_ns_prefix_ = "detect";  // NOLINT
std::string frame_id_ = "";  // NOLINT
bool use_roi_filter_;
ROIParams params_roi_;
ROIParams params_roi_2;
bool use_non_ground_segmenter_;
bool is_object_builder_open_;
int sub_pc_angle;
// ROS Subscriber
ros::Subscriber pointcloud_sub_;
// ROS Publisher
ros::Publisher ground_pub_;
ros::Publisher nonground_pub_;
ros::Publisher clusters_pub_;
ros::Publisher objects_pub_;


//hyunjin for lane publisher 0627
ros::Publisher lane_pub_;
ros::Publisher Roi_pub_;
/// @note Core components
std::unique_ptr<segmenter::BaseSegmenter> ground_remover_;
std::unique_ptr<segmenter::BaseSegmenter> segmenter_;
std::unique_ptr<object_builder::BaseObjectBuilder> object_builder_;

void OnPointCloud(const sensor_msgs::PointCloud2ConstPtr& ros_pc2) {
    common::Clock clock;

    PointICloudPtr cloud(new PointICloud);

    pcl::fromROSMsg(*ros_pc2, *cloud);

    Eigen::Matrix4f tilt_matrix = Eigen::Matrix4f::Identity();
    tilt_matrix.topLeftCorner(3, 3) = Eigen::AngleAxisf(sub_pc_angle * M_PI / 180.0f, Eigen::Vector3f::UnitY()).toRotationMatrix();

    // filtering before RANSAC (height and normal filtering)
    pcl::transformPointCloud(*cloud, *cloud, tilt_matrix);

    //pcl_conversions::toPCL(*cloud_, cloud_in);
    //ROS_INFO_STREAM(" Cloud inputs: #" << cloud->size() << " Points");

    std_msgs::Header header = ros_pc2->header;
    header.frame_id = frame_id_;
    header.stamp = ros::Time::now();

    if (use_roi_filter_) {
        roi::applyROIFilter<PointI>(params_roi_, cloud);
    }

    std::vector<PointICloudPtr> cloud_clusters;
    PointICloudPtr cloud_ground(new PointICloud);
    PointICloudPtr cloud_nonground(new PointICloud);

    ground_remover_->segment(*cloud, cloud_clusters);
    *cloud_ground = *cloud_clusters[0];
    *cloud_nonground = *cloud_clusters[1];

    // reset clusters
    cloud_clusters.clear();
    if (use_non_ground_segmenter_) {
        segmenter_->segment(*cloud_nonground, cloud_clusters);
        common::publishClustersCloud<PointI>(clusters_pub_, header,
                                             cloud_clusters);
    }

    common::publishCloud<PointI>(ground_pub_, header, *cloud_ground);
    common::publishCloud<PointI>(nonground_pub_, header, *cloud_nonground);

    if (is_object_builder_open_) {
        std::vector<autosense::ObjectPtr> objects;
        object_builder_->build(cloud_clusters, &objects);
        common::publishObjectsMarkers(
            objects_pub_, header, common::MAGENTA.rgbA, objects);
        //hyunjin
        common::publishLaneMarkers(
            lane_pub_, header, common::WHITE.rgbA);
        //jaeseung
        //common::publishRoi(
        //    Roi_pub_, header, common::WHITE.rgbA, objects);
    }
    //jaeseung
    /*if (use_roi_filter_) {
        roi::applyROIFilter<PointI>(params_roi_2, );
    }*/

    ROS_INFO_STREAM("Cloud processed. Took " << clock.takeRealTime()
                                             << "ms.\n");
}

int main(int argc, char **argv) {
    ros::init(argc, argv, "detection_node");

    // Node handle
    ros::NodeHandle nh = ros::NodeHandle(), private_nh = ros::NodeHandle("~");

    /// @brief Load ROS parameters from rosparam server
    private_nh.getParam(param_ns_prefix_ + "/frame_id", frame_id_);
    std::cout << frame_id_ << std::endl;
    std::string sub_pc_topic, pub_pc_ground_topic, pub_pc_nonground_topic,
            pub_pc_clusters_topic;
    int sub_pc_queue_size;
    private_nh.getParam(param_ns_prefix_ + "/sub_pc_topic", sub_pc_topic);
    private_nh.getParam(param_ns_prefix_ + "/sub_pc_queue_size",
                        sub_pc_queue_size);
    private_nh.getParam(param_ns_prefix_ + "/pub_pc_ground_topic",
                        pub_pc_ground_topic);
    private_nh.getParam(param_ns_prefix_ + "/pub_pc_nonground_topic",
                        pub_pc_nonground_topic);
    private_nh.getParam(param_ns_prefix_ + "/pub_pc_clusters_topic",
                        pub_pc_clusters_topic);
	private_nh.getParam(param_ns_prefix_ + "/sub_pc_angle", sub_pc_angle);

    /// @note Important to use roi filter for "Ground remover"
    private_nh.param<bool>(param_ns_prefix_ + "/use_roi_filter",
                           use_roi_filter_, false);
    params_roi_ = common::getRoiParams(private_nh, param_ns_prefix_);

    // warning ROI (jaeseung)
    //params_roi_2 = common::getRoiParams2(private_nh, param_ns_prefix_);

    // Ground remover & non-ground segmenter
    std::string ground_remover_type, non_ground_segmenter_type;
    private_nh.param<std::string>(param_ns_prefix_ + "/ground_remover_type",
                                  ground_remover_type,
                                  "GroundPlaneFittingSegmenter");
    private_nh.param<bool>(param_ns_prefix_ + "/use_non_ground_segmenter",
                           use_non_ground_segmenter_, false);
    private_nh.param<std::string>(
            param_ns_prefix_ + "/non_ground_segmenter_type",
            non_ground_segmenter_type, "RegionEuclideanSegmenter");
    SegmenterParams param =
            common::getSegmenterParams(private_nh, param_ns_prefix_);

    param.segmenter_type = ground_remover_type;
    ground_remover_ = segmenter::createGroundSegmenter(param);

    if (use_non_ground_segmenter_) {
        param.segmenter_type = non_ground_segmenter_type;
        segmenter_ = segmenter::createNonGroundSegmenter(param);
    }

    private_nh.param<bool>(param_ns_prefix_ + "/is_object_builder_open",
                           is_object_builder_open_, false);
    if (is_object_builder_open_) {
        object_builder_ = object_builder::createObjectBuilder();
        if (nullptr == object_builder_) {
            ROS_FATAL("Failed to create object_builder_.");
            return -1;
        }

        std::string pub_objects_segmented_topic , pub_lane_marker;
        pub_lane_marker = "/lane_marker";
        //std::string pub_Roi;
        private_nh.getParam(param_ns_prefix_ + "/pub_objects_segmented_topic",
                            pub_objects_segmented_topic);
        objects_pub_ = nh.advertise<visualization_msgs::MarkerArray>(
                pub_objects_segmented_topic, 1);
        //Hyunjin
        lane_pub_ = nh.advertise<visualization_msgs::Marker>(
                pub_lane_marker, 1);        
        //jaeseung
        //Roi_pub_ = nh.advertise<visualization_msgs::MarkerArray>(
        //        "/segmenter/Warning_Zone", 1);
    }

	// dbw_cmd node
	common::accel_pub = nh.advertise<std_msgs::Int16>("/dbw_cmd/Accel", 1);
	common::brake_pub = nh.advertise<std_msgs::Int16>("/dbw_cmd/Brake", 1);
	common::steer_pub = nh.advertise<std_msgs::Int16>("/dbw_cmd/Steer", 1);

	

    ground_pub_ =
            nh.advertise<sensor_msgs::PointCloud2>(pub_pc_ground_topic, 1);
    nonground_pub_ =
            nh.advertise<sensor_msgs::PointCloud2>(pub_pc_nonground_topic, 1);
    clusters_pub_ =
            nh.advertise<sensor_msgs::PointCloud2>(pub_pc_clusters_topic, 1);

    pointcloud_sub_ = nh.subscribe<sensor_msgs::PointCloud2>(
            sub_pc_topic, sub_pc_queue_size, OnPointCloud);
     
    ROS_INFO("detection_node started...");

    ros::Rate fps(10);
    while (ros::ok()) {
        ros::spinOnce();
        //fps.sleep();
    }

    ROS_INFO("detection_node exited...");

    return 0;
}
