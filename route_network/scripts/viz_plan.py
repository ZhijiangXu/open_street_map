#!/usr/bin/python
# Software License Agreement (BSD License)
#
# Copyright (C) 2012, Jack O'Quin
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of the author nor of other contributors may be
#    used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Revision $Id$

"""
Visualize route plan for geographic map.
"""

PKG_NAME = 'route_network'
import roslib; roslib.load_manifest(PKG_NAME)
import rospy

import sys
import random
import geodesy.wu_point

from geographic_msgs.msg import RouteNetwork
from geographic_msgs.msg import RouteSegment
from geographic_msgs.srv import GetRoutePlan
from geometry_msgs.msg import Point
from geometry_msgs.msg import Quaternion
from geometry_msgs.msg import Vector3
from std_msgs.msg import ColorRGBA
from visualization_msgs.msg import Marker
from visualization_msgs.msg import MarkerArray

class RouteVizNode():

    def __init__(self):
        """ROS node to visualize a route plan.
        """
        rospy.init_node('viz_routes')
        self.graph = None

        # advertise visualization marker topic
        self.pub = rospy.Publisher('visualization_marker_array',
                                   MarkerArray, latch=True)

        rospy.wait_for_service('get_geographic_map')
        self.get_plan = rospy.ServiceProxy('get_route_plan', GetRoutePlan)

        # subscribe to route network
        self.sub = rospy.Subscriber('route_network', RouteNetwork,
                                    self.graph_callback)

    def graph_callback(self, graph):
        """Handle RouteNetwork message.

        :param graph: RouteNetwork message.

        :post: self.graph = RouteNetwork message
        :post: self.points = visualization markers message.
        """
        self.graph = graph
        self.points = geodesy.wu_point.WuPointSet(graph.points)

        # select start and goal way points at random
        start, goal = random.sample(xrange(len(self.graph.points)), 2)
        start_id = graph.points[start].id
        goal_id = graph.points[goal].id
        print start_id, goal_id
        try:
            resp = self.get_plan(graph.id, start_id, goal_id)
        except rospy.ServiceException as e:
            rospy.logerr("Service call failed:", str(e))
        else:                           # get_map returned
            print resp
            if resp.success:
                self.mark_plan(resp.plan)
            else:
                rospy.logerr('get_route_plan failed, status:', str(resp.status))

    def mark_plan(self, plan):
        """Publish visualization markers for a RoutePath.

        :param plan: RoutePath message
        """
        self.plan = plan
        return
        marks = MarkerArray()
        index = 0
        for segment in self.plan.segments:
            marker = Marker(header = self.graph.header,
                            ns = 'plan_segments',
                            id = index,
                            type = Marker.LINE_STRIP,
                            action = Marker.ADD,
                            scale = Vector3(x=2.),
                            color = ColorRGBA(r=1., g=0., b=0., a=0.8),
                            lifetime = rospy.Duration())
            index += 1
            marker.points.append(self.points[segment.start.uuid].toPointXY())
            marker.points.append(self.points[segment.end.uuid].toPointXY())
            marks.markers.append(marker)

        self.pub.publish(marks)
    
def main():
    node_class = RouteVizNode()
    try:
        rospy.spin()            # wait for messages
    except rospy.ROSInterruptException: pass

if __name__ == '__main__':
    # run main function and exit
    sys.exit(main())
