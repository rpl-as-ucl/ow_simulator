#!/usr/bin/env python

# The Notices and Disclaimers for Ocean Worlds Autonomy Testbed for Exploration
# Research and Simulation can be found in README.md in the root directory of
# this repository.

import constants
import math
import datetime
import time
import rospy
from utils import is_shou_yaw_goal_in_range

def arg_parsing(req):
  if req.use_defaults :
    # Default trenching values
    delete_prev_traj=False
    target_x=2.0
    target_y=0.0
    target_z=0.3
    direction_x=0.0
    direction_y=0.0
    direction_z=1.0
    search_distance = 0.5

  else :
    delete_prev_traj = req.delete_prev_traj
    target_x = req.x
    target_y = req.y
    target_z = req.z
    direction_x = req.direction_x
    direction_y = req.direction_y
    direction_z = req.direction_z
    search_distance = req.search_distance

  return [req.use_defaults, delete_prev_traj, target_x, target_y, target_z,
          direction_x, direction_y, direction_z, search_distance]

# Approach
def pre_guarded_move(move_arm, args):
  targ_x = args[2]
  targ_y = args[3]
  targ_z = args[4]
  direction_x = args[5]
  direction_y = args[6]
  direction_z = args[7]
  search_distance = args[8]

  # STUB: GROUND HEIGHT TO BE EXTRACTED FROM DEM
  targ_elevation = -0.2
  if (targ_z+targ_elevation)==0:
    offset = search_distance
  else:
    offset = (targ_z*search_distance)/(targ_z+targ_elevation)

  # Compute shoulder yaw angle to target
  alpha = math.atan2( (targ_y+direction_y*offset)-constants.Y_SHOU, (targ_x+direction_x*offset)-constants.X_SHOU)
  h = math.sqrt(pow( (targ_y+direction_y*offset)-constants.Y_SHOU,2) + pow( (targ_x+direction_x*offset)-constants.X_SHOU,2) )
  l = constants.Y_SHOU - constants.HAND_Y_OFFSET
  beta = math.asin (l/h)

  # Move to pre move position, align shoulder yaw
  joint_goal = move_arm.get_current_joint_values()
  joint_goal[constants.J_DIST_PITCH] = 0
  joint_goal[constants.J_HAND_YAW] = 0
  joint_goal[constants.J_PROX_PITCH] = -math.pi/2
  joint_goal  [constants.J_SHOU_PITCH] = math.pi/2
  joint_goal[constants.J_SHOU_YAW] = alpha + beta

  # If out of joint range, abort
  if (is_shou_yaw_goal_in_range(joint_goal) == False):
     return False

  joint_goal[constants.J_SCOOP_YAW] = 0
  move_arm.go(joint_goal, wait=True)
  move_arm.stop()

  # Once aligned to move goal and offset, place scoop tip at surface target offset
  goal_pose = move_arm.get_current_pose().pose
  goal_pose.position.x = targ_x
  goal_pose.position.y = targ_y
  goal_pose.position.z = targ_z
  move_arm.set_pose_target(goal_pose)
  plan = move_arm.plan()
  if len(plan.joint_trajectory.points) == 0: # If no plan found, abort
     return False

  plan = move_arm.go(wait=True)
  move_arm.stop()
  move_arm.clear_pose_targets()
  print "Done planning approach of guarded_move"
  return True

def guarded_move(move_arm, args):

  direction_x = args[5]
  direction_y = args[6]
  direction_z = args[7]
  search_distance = args[8]

  # Drive scoop tip along norm vector, distance is search_distance
  goal_pose = move_arm.get_current_pose().pose
  goal_pose.position.x -= direction_x*search_distance
  goal_pose.position.y -= direction_y*search_distance
  goal_pose.position.z -= direction_z*search_distance
  move_arm.set_max_velocity_scaling_factor(0.1) # Limit speed for approach
  move_arm.set_pose_target(goal_pose)
  plan = move_arm.plan()
  if len(plan.joint_trajectory.points) == 0: # If no plan found, abort
    return False

  plan = move_arm.go(wait=True)
  move_arm.stop()
  move_arm.clear_pose_targets()
  print "Done planning safe part of guarded_move"
  return True
