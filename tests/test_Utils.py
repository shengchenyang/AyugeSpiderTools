import json
from ayugespidertools.common.Utils import ToolsForAyu


def test_extract_with_json():
    josn_data_ori = '''{"code":"0","message":"success","data":{"thumb_up":0,"im":33,"gitChat_thumb_up":0,"avatarUrl":"https://profile.csdnimg.cn/D/6/8/2_Ayuge2","invitation":0,"gitChat_system":0,"GlobalSwitch":{"private_message_who_follows_me":true,"email_commit_receive":true,"interactive_follow":true,"email_collect_receive":true,"system_digital":true,"private_message_stranger":true,"email_support_receive":true,"interactive_like":true,"interactive_comment_digital":true,"system":true,"interactive_like_digital":true,"interactive_follow_digital":true,"email_follow_receive":true,"interactive_comment":true,"private_message_who_me_follows":true,"announcement_digital":true,"email":true,"announcement":true},"edu_thumb_up":0,"blink_thumb_up":0,"follow":0,"totalCount":34,"coupon_order":0,"edu_comment":0,"edu_system":0,"system":1,"comment":0,"blink_comment":0,"gitChat_comment":0},"status":true}'''

    json_data_example = {
        "code": "0",
        "message": "success",
        "data": {
            "thumb_up": 0,
            "im": 33,
            "gitChat_thumb_up": 0,
            "avatarUrl": "https://profile.csdnimg.cn/D/6/8/2_Ayuge2",
            "invitation": 0, "gitChat_system": 0,
            "GlobalSwitch": {
                "private_message_who_follows_me": True,
                "email_commit_receive": True,
                "interactive_follow": True,
                "email_collect_receive": True,
                "system_digital": True,
                "private_message_stranger": True,
                "email_support_receive": True,
                "interactive_like": True,
                "interactive_comment_digital": True,
                "system": True,
                "interactive_like_digital": True,
                "interactive_follow_digital": True,
                "email_follow_receive": True,
                "interactive_comment": True,
                "private_message_who_me_follows": True,
                "announcement_digital": True,
                "email": True,
                "announcement": True
            },
            "edu_thumb_up": 0,
            "blink_thumb_up": 0,
            "follow": 0,
            "totalCount": 34,
            "coupon_order": 0,
            "edu_comment": 0,
            "edu_system": 0,
            "system": 1,
            "comment": 0,
            "blink_comment": 0,
            "gitChat_comment": 0,

            "my_add_list": [],
            "my_add_dict": {},
        },
        "status": True
    }
    res = ToolsForAyu.extract_with_json(json_data=json_data_example, query=["data", "im"])
    print("rrrrr", type(res), res)

    res = ToolsForAyu.extract_with_json(json_data=json_data_example, query=["data", "GlobalSwitch", "announcement_ayu"])
    print("rrrrr", type(res), res)

    res = ToolsForAyu.extract_with_json(json_data=json_data_example, query=["data", "my_add_list"])
    print("rrrrr", type(res), res)

    res = ToolsForAyu.extract_with_json(json_data=json_data_example, query=["data", "my_add_dict"])
    print("rrrrr", type(res), res)

    assert True
