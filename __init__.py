bl_info = {
    "name": "Dynamic Parent",
    "description": "Allows to create and disable an animated ChildOf constraint",
    "author": "Roman Volodin, roman.volodin@gmail.com // Nathan Miguel, nathanmiguel.contato@gmail.com,Sav Martin",
    "version": (0, 8, 0),
    "blender": (2, 80, 0),
    "location": "3D View > Tools",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "",
    "tracker_url": "",
    "category": ""
}
 
import bpy
import mathutils


from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       )
from bpy.types import (Panel,
                       Menu,
                       Operator,
                       PropertyGroup,
                       )

# dp_keyframe_insert_*** functions  
def dp_keyframe_insert_obj(obj):
    obj.keyframe_insert(data_path="location")
    if obj.rotation_mode == 'QUATERNION':
        obj.keyframe_insert(data_path="rotation_quaternion")
    elif obj.rotation_mode == 'AXIS_ANGLE':
        obj.keyframe_insert(data_path="rotation_axis_angle")
    else:
        obj.keyframe_insert(data_path="rotation_euler")
    obj.keyframe_insert(data_path="scale")

def dp_keyframe_insert_pbone(arm, pbone):
    arm.keyframe_insert(data_path='pose.bones["'+pbone.name+'"].location')
    if pbone.rotation_mode == 'QUATERNION':
        arm.keyframe_insert(data_path='pose.bones["'+pbone.name+'"].rotation_quaternion')
    elif pbone.rotation_mode == 'AXIS_ANGLE':
        arm.keyframe_insert(data_path='pose.bones["'+pbone.name+'"].rotation_axis_angel')
    else:
        arm.keyframe_insert(data_path='pose.bones["'+pbone.name+'"].rotation_euler')
    arm.keyframe_insert(data_path='pose.bones["'+pbone.name+'"].scale')

def dp_create_dynamic_parent_obj(op):
    obj = bpy.context.active_object
    scn = bpy.context.scene
    list_selected_obj = bpy.context.selected_objects

    if len(list_selected_obj) == 2:
        i = list_selected_obj.index(obj)
        list_selected_obj.pop(i)
        parent_obj = list_selected_obj[0]

        dp_keyframe_insert_obj(obj)
        bpy.ops.object.constraint_add_with_targets(type='CHILD_OF')
        last_constraint = obj.constraints[-1]

        if parent_obj.type == 'ARMATURE':
            last_constraint.subtarget = parent_obj.data.bones.active.name
            last_constraint.name = "DP_"+last_constraint.target.name+"."+last_constraint.subtarget
        else:
            last_constraint.name = "DP_"+last_constraint.target.name

        #bpy.ops.constraint.childof_set_inverse(constraint=""+last_constraint.name+"", owner='OBJECT')
        C = bpy.context.copy()
        C["constraint"] = last_constraint
        bpy.ops.constraint.childof_set_inverse(C, constraint=last_constraint.name, owner='OBJECT')

        current_frame = scn.frame_current
        scn.frame_current = current_frame-1
        obj.constraints[last_constraint.name].influence = 0
        obj.keyframe_insert(data_path='constraints["'+last_constraint.name+'"].influence')

        scn.frame_current = current_frame
        obj.constraints[last_constraint.name].influence = 1
        obj.keyframe_insert(data_path='constraints["'+last_constraint.name+'"].influence')

        for ob in list_selected_obj:
            ob.select_set(False)

        obj.select_set(True)
    else:
        op.report({'ERROR'}, "Two objects must be selected")

def dp_create_dynamic_parent_pbone(op):
    arm = bpy.context.active_object
    pbone = bpy.context.active_pose_bone
    scn = bpy.context.scene
    list_selected_obj = bpy.context.selected_objects

    if len(list_selected_obj) == 2 or len(list_selected_obj) == 1:
        if len(list_selected_obj) == 2:
            i = list_selected_obj.index(arm)
            list_selected_obj.pop(i)
            parent_obj = list_selected_obj[0]
            if parent_obj.type == 'ARMATURE':
                parent_obj_pbone = parent_obj.data.bones.active
        else:
            parent_obj = arm
            selected_bones = bpy.context.selected_pose_bones
            selected_bones.remove(pbone)
            parent_obj_pbone = selected_bones[0]

#        debuginfo = '''
#        DEBUG INFO:
#        obj = {}
#        pbone = {}
#        parent = {}
#        parent_bone = {}
#        '''
#        print(debuginfo.format(arm, pbone, parent_obj, parent_obj_pbone))

        dp_keyframe_insert_pbone(arm, pbone)
        bpy.ops.pose.constraint_add_with_targets(type='CHILD_OF')
        last_constraint = pbone.constraints[-1]

        if parent_obj.type == 'ARMATURE':
            last_constraint.subtarget = parent_obj_pbone.name
            last_constraint.name = "DP_"+last_constraint.target.name+"."+last_constraint.subtarget
        else:
            last_constraint.name = "DP_"+last_constraint.target.name

        #bpy.ops.constraint.childof_set_inverse(constraint=""+last_constraint.name+"", owner='BONE')
        C = bpy.context.copy()
        C["constraint"] = last_constraint
        bpy.ops.constraint.childof_set_inverse(C, constraint=last_constraint.name, owner='BONE')

        current_frame = scn.frame_current
        scn.frame_current = current_frame-1
        pbone.constraints[last_constraint.name].influence = 0
        arm.keyframe_insert(data_path='pose.bones["'+pbone.name+'"].constraints["'+last_constraint.name+'"].influence')

        scn.frame_current = current_frame
        pbone.constraints[last_constraint.name].influence = 1
        arm.keyframe_insert(data_path='pose.bones["'+pbone.name+'"].constraints["'+last_constraint.name+'"].influence')  
    else:
        op.report({'ERROR'}, "Two objects must be selected")

def dp_disable_dynamic_parent_obj(op):
    obj = bpy.context.active_object
    scn = bpy.context.scene

    if len(obj.constraints) == 0:
        op.report({'ERROR'}, "Object has no constraint")
    else:
        last_constraint = obj.constraints[-1]

        if "DP_" in last_constraint.name:
            current_frame = scn.frame_current
            scn.frame_current = current_frame-1
            obj.constraints[last_constraint.name].influence = 1
            obj.keyframe_insert(data_path='constraints["'+last_constraint.name+'"].influence')

            scn.frame_current = current_frame
            obj.constraints[last_constraint.name].influence = 0
            obj.keyframe_insert(data_path='constraints["'+last_constraint.name+'"].influence')

            loc, rot, scale = obj.matrix_world.decompose()
            rot_euler = rot.to_euler()

            current_frame = scn.frame_current
            scn.frame_current = current_frame - 1
            dp_keyframe_insert_obj(obj)

            scn.frame_current = current_frame
            obj.location = loc
            obj.rotation_euler = rot_euler
            obj.scale = scale
            dp_keyframe_insert_obj(obj)
        else:
            op.report({'ERROR'}, "Object has no Dynamic Parent constraint")

def dp_disable_dynamic_parent_pbone(op):
    arm = bpy.context.active_object
    pbone = bpy.context.active_pose_bone
    scn = bpy.context.scene

    if len(pbone.constraints) == 0:
        op.report({'ERROR'}, "Bone has no constraint")
    else:
        last_constraint = pbone.constraints[-1]

        current_frame = scn.frame_current
        scn.frame_current = current_frame - 1
        pbone.constraints[last_constraint.name].influence = 1
        arm.keyframe_insert(data_path='pose.bones["'+pbone.name+'"].constraints["'+last_constraint.name+'"].influence')

        scn.frame_current = current_frame
        pbone.constraints[last_constraint.name].influence = 0
        arm.keyframe_insert(data_path='pose.bones["'+pbone.name+'"].constraints["'+last_constraint.name+'"].influence')

        final_matrix = pbone.matrix @ arm.matrix_world

        current_frame = scn.frame_current
        scn.frame_current = current_frame - 1
        dp_keyframe_insert_pbone(arm, pbone)

        scn.frame_current = current_frame
        pbone.matrix = final_matrix
        dp_keyframe_insert_pbone(arm, pbone)

def dp_clear(obj, pbone):
    dp_curves = []
    dp_keys = []
    for fcurve in obj.animation_data.action.fcurves:
        if "constraints" in fcurve.data_path and "DP_" in fcurve.data_path:
            dp_curves.append(fcurve)

    for f in dp_curves:
        for key in f.keyframe_points:
            dp_keys.append(key.co[0])

    dp_keys = list(set(dp_keys))
    dp_keys.sort()

    for fcurve in obj.animation_data.action.fcurves[:]:
        # Removing constraints fcurves
        if fcurve.data_path.startswith("constraints") and "DP_" in fcurve.data_path:
            obj.animation_data.action.fcurves.remove(fcurve)
        # Removing keys for loc, rot, scale fcurves
        else:
            for frame in dp_keys:
                for key in fcurve.keyframe_points[:]:
                    if key.co[0] == frame:
                        fcurve.keyframe_points.remove(key)
            if not fcurve.keyframe_points:
                obj.animation_data.action.fcurves.remove(fcurve)

    # Removing constraints
    if pbone:
        obj = pbone
    for const in obj.constraints[:]:
        if const.name.startswith("DP_"):
            obj.constraints.remove(const)

class DpCreateConstraint(bpy.types.Operator):
    """Create a new animated Child Of constraint"""
    bl_idname = "dp.create"
    bl_label = "Create Constraint"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = bpy.context.active_object

        if obj.type == 'ARMATURE':
            obj = bpy.context.active_pose_bone

            if len(obj.constraints) == 0:
                dp_create_dynamic_parent_pbone(self)
            else:
                if "DP_" in obj.constraints[-1].name and obj.constraints[-1].influence == 1:
                    dp_disable_dynamic_parent_pbone(self)
                dp_create_dynamic_parent_pbone(self)
        else:        
            if len(obj.constraints) == 0:
                dp_create_dynamic_parent_obj(self)
            else:
                if "DP_" in obj.constraints[-1].name and obj.constraints[-1].influence == 1:
                    dp_disable_dynamic_parent_obj(self)
                dp_create_dynamic_parent_obj(self)

        return {'FINISHED'}

class DpDisableConstraint(bpy.types.Operator):
    """Disable the current animated Child Of constraint"""
    bl_idname = "dp.disable"
    bl_label = "Disable Constraint"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = bpy.context.active_object
        if obj.type == 'ARMATURE':
            dp_disable_dynamic_parent_pbone(self)
        else:
            dp_disable_dynamic_parent_obj(self)
        return {'FINISHED'}

class DpClear(bpy.types.Operator):
    """Clear Dynamic Parent constraints"""
    bl_idname = "dp.clear"
    bl_label = "Clear Dynamic Parent"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pbone = None
        obj = bpy.context.active_object
        if obj.type == 'ARMATURE':
            pbone = bpy.context.active_pose_bone

        dp_clear(obj, pbone)

        return {'FINISHED'}

class DpBake(bpy.types.Operator):
    """Bake Dynamic Parent animation"""
    bl_idname = "dp.bake"
    bl_label = "Bake Dynamic Parent"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = bpy.context.active_object
        scn = bpy.context.scene

        if obj.type == 'ARMATURE':
            obj = bpy.context.active_pose_bone
            bpy.ops.nla.bake(frame_start=scn.frame_start,
                             frame_end=scn.frame_end, step=1,
                             only_selected=True, visual_keying=False,
                             clear_constraints=False, clear_parents=False,
                             bake_types={'POSE'})
            # Removing constraints
            for const in obj.constraints[:]:
                if const.name.startswith("DP_"):
                    obj.constraints.remove(const)
        else:
            bpy.ops.nla.bake(frame_start=scn.frame_start,
                             frame_end=scn.frame_end, step=1,
                             only_selected=True, visual_keying=False,
                             clear_constraints=False, clear_parents=False,
                             bake_types={'OBJECT'})
            # Removing constraints
            for const in obj.constraints[:]:
                if const.name.startswith("DP_"):
                    obj.constraints.remove(const)

        return {'FINISHED'}

class DpClearMenu(bpy.types.Menu):
    """Clear or bake Dynamic Parent constraints"""
    bl_label = "Clear Dynamic Parent?"
    bl_idname = "dp.clear_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("dp.clear", text="Clear", icon="X")
        layout.operator("dp.bake", text="Bake and clear", icon="REC")

# ------------------------------------------------------------------------
#    Panel in Object Mode
# ------------------------------------------------------------------------   

class DpUI(Panel):
    """User interface for Dynamic Parent addon"""
    bl_label = "Dynamic Parent"
    bl_idname = "OBJECT_PT_custom_panel"
    bl_space_type = "VIEW_3D"   
    bl_region_type = "UI"
    bl_category = "DP"   


    @classmethod
    def poll(self,context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        row = layout.column(align=True)
        row.operator("dp.create", text="Create", icon="KEY_HLT")
        row.operator("dp.disable", text="Disable", icon="KEY_DEHLT")
        row.menu("dp.clear_menu", text="Clear")

# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------
        
classes = (
    DpUI,
    DpBake,
    DpClear,
    DpClearMenu,
    DpCreateConstraint,
    DpDisableConstraint,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)


if __name__ == "__main__":
    register()