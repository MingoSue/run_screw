(function(t){function e(e){for(var n,o,i=e[0],c=e[1],u=e[2],p=0,f=[];p<i.length;p++)o=i[p],a[o]&&f.push(a[o][0]),a[o]=0;for(n in c)Object.prototype.hasOwnProperty.call(c,n)&&(t[n]=c[n]);l&&l(e);while(f.length)f.shift()();return s.push.apply(s,u||[]),r()}function r(){for(var t,e=0;e<s.length;e++){for(var r=s[e],n=!0,i=1;i<r.length;i++){var c=r[i];0!==a[c]&&(n=!1)}n&&(s.splice(e--,1),t=o(o.s=r[0]))}return t}var n={},a={app:0},s=[];function o(e){if(n[e])return n[e].exports;var r=n[e]={i:e,l:!1,exports:{}};return t[e].call(r.exports,r,r.exports,o),r.l=!0,r.exports}o.m=t,o.c=n,o.d=function(t,e,r){o.o(t,e)||Object.defineProperty(t,e,{enumerable:!0,get:r})},o.r=function(t){"undefined"!==typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(t,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(t,"__esModule",{value:!0})},o.t=function(t,e){if(1&e&&(t=o(t)),8&e)return t;if(4&e&&"object"===typeof t&&t&&t.__esModule)return t;var r=Object.create(null);if(o.r(r),Object.defineProperty(r,"default",{enumerable:!0,value:t}),2&e&&"string"!=typeof t)for(var n in t)o.d(r,n,function(e){return t[e]}.bind(null,n));return r},o.n=function(t){var e=t&&t.__esModule?function(){return t["default"]}:function(){return t};return o.d(e,"a",e),e},o.o=function(t,e){return Object.prototype.hasOwnProperty.call(t,e)},o.p="/";var i=window["webpackJsonp"]=window["webpackJsonp"]||[],c=i.push.bind(i);i.push=e,i=i.slice();for(var u=0;u<i.length;u++)e(i[u]);var l=c;s.push([0,"chunk-vendors"]),r()})({0:function(t,e,r){t.exports=r("56d7")},"56d7":function(t,e,r){"use strict";r.r(e);r("cadf"),r("551c"),r("f751"),r("097d");var n=r("2b0e"),a=function(){var t=this,e=t.$createElement,r=t._self._c||e;return r("div",{attrs:{id:"app"}},[r("router-view")],1)},s=[],o=(r("7c55"),r("2877")),i={},c=Object(o["a"])(i,a,s,!1,null,null,null),u=c.exports,l=r("8c4f"),p=function(){var t=this,e=t.$createElement,r=t._self._c||e;return r("div",{staticClass:"home"},[r("Row",{staticClass:"row_area",attrs:{gutter:15}},[r("Col",{attrs:{span:"12"}},[r("Card",{staticClass:"show_area",staticStyle:{height:"320px"}},[r("p",{staticClass:"title",attrs:{slot:"title"},slot:"title"},[r("Icon",{attrs:{size:"55",type:"ios-speedometer-outline"}}),t._v("转速")],1),r("p",[t._v("\n            "+t._s(Math.abs(t.speed))+"rpm\n          ")])])],1),r("Col",{attrs:{span:"12"}},[r("Card",{staticClass:"show_area",staticStyle:{height:"320px"}},[r("p",{staticClass:"title",attrs:{slot:"title"},slot:"title"},[r("Icon",{attrs:{size:"55",type:"ios-swap"}}),t._v("扭矩")],1),r("div",[t._v("\n            "+t._s(Math.abs(t.weight))+"nm\n          ")])])],1)],1),r("Row",{staticClass:"row_area",attrs:{gutter:15}},[r("Col",{attrs:{span:"12"}},[r("Card",{staticClass:"show_area",staticStyle:{height:"320px"}},[r("p",{staticClass:"title",attrs:{slot:"title"},slot:"title"},[r("Icon",{attrs:{size:"55",type:"ios-film-outline"}}),t._v("转向")],1),r("div",[t._v("\n            "+t._s(t.direction?"顺时针":"逆时针")+"\n          ")])])],1),r("Col",{attrs:{span:"12"}},[r("Card",{staticClass:"show_area",staticStyle:{height:"320px"}},[r("p",{staticClass:"title",attrs:{slot:"title"},slot:"title"},[r("Icon",{attrs:{size:"55",type:"ios-flash-outline"}}),t._v("电流")],1),r("div",[t._v("\n            "+t._s(t.current)+"mA\n          ")])])],1)],1),r("Row",{staticClass:"row_area bottom_area",attrs:{gutter:20}},[r("Col",{attrs:{span:"6"}},[r("Card",{staticStyle:{height:"160px"}},[r("p",{staticClass:"head_title",attrs:{slot:"title"},slot:"title"},[t._v("开关")]),r("i-switch",{attrs:{size:"large"},on:{"on-change":function(e){return t.change(e,"on_off")}},model:{value:t.on_off,callback:function(e){t.on_off=e},expression:"on_off"}})],1)],1),r("Col",{staticClass:"turn_to_area",attrs:{span:"6"}},[r("Card",{staticStyle:{height:"160px"}},[r("p",{staticClass:"head_title",attrs:{slot:"title"},slot:"title"},[t._v("转向")]),r("span",[t._v("反向")]),r("i-switch",{staticClass:"turn_to",attrs:{size:"large"},on:{"on-change":function(e){return t.change(e,"direction")}},model:{value:t.direction_sitch,callback:function(e){t.direction_sitch=e},expression:"direction_sitch"}}),r("span",[t._v("正向")])],1)],1),r("Col",{staticClass:"speed",attrs:{span:"6"}},[r("Card",{staticStyle:{height:"160px"}},[r("p",{staticClass:"head_title",attrs:{slot:"title"},slot:"title"},[t._v("转速")]),r("Row",{attrs:{gutter:15}},[r("Col",{attrs:{span:"8"}},[r("Button",{attrs:{type:1==t.currentSpeed?"primary":"default"},on:{click:function(e){return t.btnClick(1)}}},[t._v("20%")])],1),r("Col",{attrs:{span:"8"}},[r("Button",{attrs:{type:2==t.currentSpeed?"primary":"default"},on:{click:function(e){return t.btnClick(2)}}},[t._v("50%")])],1),r("Col",{attrs:{span:"8"}},[r("Button",{attrs:{type:3==t.currentSpeed?"primary":"default"},on:{click:function(e){return t.btnClick(3)}}},[t._v("100%")])],1)],1)],1)],1),r("Col",{staticClass:"speed",attrs:{span:"6"}},[r("Card",{staticStyle:{height:"160px"}},[r("p",{staticClass:"head_title",attrs:{slot:"title"},slot:"title"},[t._v("扭矩")]),r("Row",{attrs:{gutter:15}},[r("Col",{attrs:{span:"6"}},[r("Button",{attrs:{type:1==t.currentTorque?"primary":"default"},on:{click:function(e){return t.torqueClick(1)}}},[t._v("2")])],1),r("Col",{attrs:{span:"6"}},[r("Button",{attrs:{type:2==t.currentTorque?"primary":"default"},on:{click:function(e){return t.torqueClick(2)}}},[t._v("5")])],1),r("Col",{attrs:{span:"6"}},[r("Button",{attrs:{type:3==t.currentTorque?"primary":"default"},on:{click:function(e){return t.torqueClick(3)}}},[t._v("8")])],1),r("Col",{attrs:{span:"6"}},[r("Button",{attrs:{type:4==t.currentTorque?"primary":"default"},on:{click:function(e){return t.torqueClick(4)}}},[t._v("10")])],1)],1)],1)],1)],1)],1)},f=[],h=(r("96cf"),r("3b8d")),d=r("bc3a"),v=r.n(d),g="http://192.168.122.97:8000";v.a.defaults.headers.post["Content-Type"]="application/json",v.a.defaults.withCredentials=!0,v.a.defaults.timeout=1e4;var _=function(){var t=Object(h["a"])(regeneratorRuntime.mark(function t(e,r,n){var a;return regeneratorRuntime.wrap(function(t){while(1)switch(t.prev=t.next){case 0:t.prev=0,t.t0=e,t.next="get"===t.t0?4:"delete"===t.t0?8:12;break;case 4:return t.next=6,v.a.get(g+r,{params:n});case 6:return a=t.sent,t.abrupt("break",15);case 8:return t.next=10,v.a.delete(g+r,{data:n});case 10:return a=t.sent,t.abrupt("break",15);case 12:return t.next=14,v.a[e](g+r,n);case 14:a=t.sent;case 15:return t.abrupt("return",a);case 18:return t.prev=18,t.t1=t["catch"](0),console.log(t.t1),t.abrupt("return",Promise.reject(t.t1));case 22:case"end":return t.stop()}},t,null,[[0,18]])}));return function(e,r,n){return t.apply(this,arguments)}}(),C={name:"home",data:function(){return{on_off:!1,direction_sitch:!1,speed_20:!0,speed_50:!0,speed_100:!0,currentSpeed:0,direction:0,current:0,speed:0,weight:0,currentTorque:0}},created:function(){var t=this;this.getData(),this.getConfig(),this.inter=setInterval(function(){t.getData(),t.getConfig()},2e3)},methods:{btnClick:function(t){this.currentSpeed=t,this.change("btn","speed")},torqueClick:function(t){this.currentTorque=t,this.change("btn","torque")},getConfig:function(){var t=Object(h["a"])(regeneratorRuntime.mark(function t(){var e,r,n,a,s,o;return regeneratorRuntime.wrap(function(t){while(1)switch(t.prev=t.next){case 0:return t.prev=0,t.next=3,_("get","/test/screwconfig");case 3:e=t.sent,e&&(r=e.data,n=r.speed,a=r.power,s=r.direction,o=r.n,this.on_off=1==a,this.currentSpeed=(.2==n?1:.5==n&&2)||1==n&&3,this.direction=1===s,this.direction_sitch=1==s,this.currentTorque=(2==o?1:5==o&&2)||8==o&&3||10==o&&4),t.next=9;break;case 7:t.prev=7,t.t0=t["catch"](0);case 9:case"end":return t.stop()}},t,this,[[0,7]])}));function e(){return t.apply(this,arguments)}return e}(),change:function(){var t=Object(h["a"])(regeneratorRuntime.mark(function t(e,r){var n,a;return regeneratorRuntime.wrap(function(t){while(1)switch(t.prev=t.next){case 0:return t.prev=0,n={},"on_off"==r&&(n.power=this.on_off?1:0),"direction"==r&&(n.direction=this.direction_sitch?1:-1),"speed"==r&&(n.speed=(1===this.currentSpeed?.2:2===this.currentSpeed&&.5)||3===this.currentSpeed&&1||0),"torque"==r&&(n.n=(1===this.currentTorque?2:2===this.currentTorque&&5)||3===this.currentTorque&&8||4===this.currentTorque&&10||0),t.next=8,_("post","/test/screwconfig",n);case 8:a=t.sent,a&&(this.message("更新成功 ！","success"),console.log(a)),t.next=14;break;case 12:t.prev=12,t.t0=t["catch"](0);case 14:case"end":return t.stop()}},t,this,[[0,12]])}));function e(e,r){return t.apply(this,arguments)}return e}(),getData:function(){var t=Object(h["a"])(regeneratorRuntime.mark(function t(){var e,r,n,a,s;return regeneratorRuntime.wrap(function(t){while(1)switch(t.prev=t.next){case 0:return t.prev=0,t.next=3,_("get","/test/screw");case 3:e=t.sent,e&&(r=e.data,n=r.current,r.direction,a=r.speed,s=r.weight,this.current=n,this.speed=a,this.weight=s),console.log(e),t.next=11;break;case 8:t.prev=8,t.t0=t["catch"](0),console.log(t.t0);case 11:case"end":return t.stop()}},t,this,[[0,8]])}));function e(){return t.apply(this,arguments)}return e}()},components:{}},b=C,m=(r("de16"),Object(o["a"])(b,p,f,!1,null,null,null)),w=m.exports;n["a"].use(l["a"]);var y=new l["a"]({mode:"history",base:"/",routes:[{path:"/",name:"home",component:w}]}),k=r("2f62");n["a"].use(k["a"]);var x=new k["a"].Store({state:{},mutations:{},actions:{}}),S=r("2b1a"),q=r("117e"),j=r("01f8"),O=r("0347"),T=r("d3b2"),R=r("bbbe"),B=r("6ead"),M=r("ae14");r("c62c");n["a"].component("i-switch",M["a"]),n["a"].component("Col",B["a"]),n["a"].component("Row",R["a"]),n["a"].component("Icon",T["a"]),n["a"].component("Card",O["a"]),n["a"].component("Button",j["a"]),n["a"].prototype.$Message=q["a"],n["a"].prototype.$Loading=S["a"],n["a"].prototype.loading=function(t){this.$Loading[t]({color:"#5cb85c",failedColor:"#f0ad4e",height:12})},n["a"].prototype.message=function(t,e){var r;switch(e){case 0:r="warning";break;case 99:r="warning";break;case 200:r="success";break;case 500:r="error";break;default:r=e}this.$Message[r]({content:t})},n["a"].config.productionTip=!1,new n["a"]({router:y,store:x,render:function(t){return t(u)}}).$mount("#app")},"5c48":function(t,e,r){},"7c55":function(t,e,r){"use strict";var n=r("5c48"),a=r.n(n);a.a},c62c:function(t,e,r){},de16:function(t,e,r){"use strict";var n=r("f3e7"),a=r.n(n);a.a},f3e7:function(t,e,r){}});