// module.paths.push("/root/mydownload/node_config/node_global/lib/node_modules")
// module.paths.push("D:\\Program Files\\nodejs\\node_global\\node_modules")
const {createCanvas, Image} = require('canvas')


// js 中原本的 canvas 相关操作内容
function ori_canvas(t, e) {
    // img
    t = t['$_CGz'],
    // canvas
    e = e['$_CGz'];
    var n = t['width']
        , r = t['height']
        , i = h['createElement']('canvas');
    i['width'] = n,
            i['height'] = r;

    var o = i['getContext']('2d');
    o['drawImage'](t, 0, 0);
    var s = e['getContext']('2d');

    e['height'] = r,
        e['width'] = 260;
    Ut = [
        39,
        38,
        48,
        49,
        41,
        40,
        46,
        47,
        35,
        34,
        50,
        51,
        33,
        32,
        28,
        29,
        27,
        26,
        36,
        37,
        31,
        30,
        44,
        45,
        43,
        42,
        12,
        13,
        23,
        22,
        14,
        15,
        21,
        20,
        8,
        9,
        25,
        24,
        6,
        7,
        3,
        2,
        0,
        1,
        11,
        10,
        4,
        5,
        19,
        18,
        16,
        17
    ];
    for (var a = r / 2, _ = 0; _ < 52; _ += 1) {
        var c = Ut[_] % 26 * 12 + 1
            , u = 25 < Ut[_] ? a : 0
            , l = o[$_CJFA(27)](c, u, 10, a);
        s[$_CJFA(81)](l, _ % 26 * 10, 25 < _ ? a : 0);
    };
}


// node-canvas 的实现方法示例
function node_canvas(need_deal_img) {
    // img
    // t = t['$_CGz'],
    t = new Image();
    t.src = need_deal_img;

    // canvas
    // e = e['$_CGz'];
    e = createCanvas(260, 160)
    var n = t['width']
        , r = t['height']
    //     , i = h['createElement']('canvas');
    // i['width'] = n,
    //     i['height'] = r;
    i = createCanvas(n, r)

    // var o = i['getContext']('2d');
    var o = i.getContext('2d');
    // o['drawImage'](t, 0, 0);

    o.drawImage(t, 0, 0, 312, 160)
    // var s = e['getContext']('2d');
    var s = e.getContext('2d');

    e['height'] = r,
        e['width'] = 260;
    Ut = [
        39,
        38,
        48,
        49,
        41,
        40,
        46,
        47,
        35,
        34,
        50,
        51,
        33,
        32,
        28,
        29,
        27,
        26,
        36,
        37,
        31,
        30,
        44,
        45,
        43,
        42,
        12,
        13,
        23,
        22,
        14,
        15,
        21,
        20,
        8,
        9,
        25,
        24,
        6,
        7,
        3,
        2,
        0,
        1,
        11,
        10,
        4,
        5,
        19,
        18,
        16,
        17
    ];
    for (var a = r / 2, _ = 0; _ < 52; _ += 1) {
        var c = Ut[_] % 26 * 12 + 1
            , u = 25 < Ut[_] ? a : 0
            // , l = o["getImageData"](c, u, 10, a);
            , l = o.getImageData(c, u, 10, a);
        // s["putImageData"](l, _ % 26 * 10, 25 < _ ? a : 0);
        s.putImageData(l, _ % 26 * 10, 25 < _ ? a : 0);
    };

    console.log(e.toDataURL());
}


// 测试调用
node_canvas("../../docs/image/geetest.jpg")
