from launch import LaunchDescription
import launch_ros.actions


def generate_launch_description():
    return LaunchDescription([
        launch_ros.actions.Node(
            # the name of the executable is set in CMakeLists.txt, towards the end of
            # the file, in add_executable(...) and the directives following it
            package='artiv_mission_navi', node_executable='mission_navi_node', output='screen'),
    ])
