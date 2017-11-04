from .snapping_utils import *
from .driver_utils import split_path
from .insert_keyframe import insert_keyframe

def snap_ik_fk(rig,way,switch_prop,
                    FK_root,FK_tip,
                    IK_last,IK_tip,IK_pole,
                    FK_mid=None,
                    full_snapping=True,
                    invert=False,
                    ik_fk_layer=None,
                    auto_switch=True):

    armature = rig.data
    poseBone = rig.pose.bones
    dataBone = rig.data.bones

    print('######### FK mid',FK_mid)

    switch_bone,switch_prop_name = split_path(switch_prop)

    if not FK_mid :
        print('no fk mid')
        FK_mid = [poseBone.get(b.name) for b in IKFK_chain.FK_mid]

    IK_mid_chain = IK_last.parent_recursive
    IK_root = IK_mid_chain[len(FK_mid)-1]
    IK_mid= IK_mid_chain[:len(FK_mid)-1]

    IK_mid.reverse()
    IK_mid.append(IK_last)

    for c in IK_last.constraints :
        if c.type == 'IK':
            ik_len = c.chain_count
            break

    IK_match = IK_mid_chain[ik_len-2]

    fk_chain = [FK_root]+FK_mid
    fk_chain.reverse()
    FK_match = fk_chain[ik_len-1]

    #######FK2IK
    if way == 'to_FK' :
        FK_root.matrix = IK_root.matrix
        FK_root.scale[0],FK_root.scale[2] =1,1
        FK_root.location = (0,0,0)
        bpy.ops.pose.visual_transform_apply()

        for i,fk_bone in enumerate(FK_mid) :
            fk_bone.matrix = IK_mid[i].matrix
            fk_bone.scale[0],fk_bone.scale[2] =1,1
            fk_bone.location = (0,0,0)
            bpy.ops.pose.visual_transform_apply()

        FK_tip.matrix = IK_tip.matrix
        FK_tip.scale[0],FK_tip.scale[2] =1,1
        FK_tip.location = (0,0,0)
        bpy.ops.pose.visual_transform_apply()

        #Rigify support
        if FK_root.get('stretch_length'):
            FK_root['stretch_length'] = IK_mid.length/IK_mid.bone.length

        invert_switch = invert*1.0

        if ik_fk_layer :
            layer_hide = ik_fk_layer[1]
            layer_show = ik_fk_layer[0]

        dataBone.active = FK_root.bone

    #######IK2FK
    elif way == 'to_IK' :
        #mute IK constraint
        for c in IK_last.constraints :
            if c.type == 'IK' :
                c.mute = True

        IK_tip.matrix = FK_tip.matrix
        bpy.ops.pose.visual_transform_apply()

        if full_snapping :
            IK_root.matrix = FK_root.matrix
            IK_root.scale[0],IK_root.scale[2] = 1,1
            IK_root.location = (0,0,0)
            bpy.ops.pose.visual_transform_apply()

            for i,ik_bone in enumerate(IK_mid):
                print('full snapping')
                ik_bone.matrix = FK_mid[i].matrix
                ik_bone.scale[0],ik_bone.scale[2] = 1,1
                #ik_bone.scale[1] = FK_mid[i].length/ik_bone.length
                ik_bone.location = (0,0,0)
                bpy.ops.pose.visual_transform_apply()

        for c in IK_last.constraints :
            if c.type == 'IK' :
                c.mute = False
        bpy.ops.pose.visual_transform_apply()

        #else :
        match_pole_target(IK_match,IK_last,IK_pole,FK_match,(IK_root.length+IK_last.length))
        bpy.ops.pose.visual_transform_apply()


        invert_switch = (not invert)*1.0
        #setattr(IKFK_chain,'layer_switch',0)

        dataBone.active = IK_tip.bone

        if ik_fk_layer :
            layer_hide = ik_fk_layer[0]
            layer_show = ik_fk_layer[1]

    if ik_fk_layer and auto_switch:
        setattr(poseBone.get(switch_bone),'["%s"]'%switch_prop_name,invert_switch)

        rig.data.layers[layer_hide] = False
        rig.data.layers[layer_show] = True

    ###settings keyframe_points
    keyBone = (FK_root,FK_tip,IK_tip,IK_pole)

    if bpy.context.scene.tool_settings.use_keyframe_insert_auto:
        if not rig.animation_data:
            rig.animation_data_create()

        rig.keyframe_insert(data_path=switch_prop,group=switch_bone)

        for b in keyBone :
            insert_keyframe(b)
        for b in FK_mid :
            insert_keyframe(b)
        for b in IK_mid :
            insert_keyframe(b)
