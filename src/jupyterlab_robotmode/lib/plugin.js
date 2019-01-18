"use strict";
/*
  Copyright (c) 2018 Georgia Tech Research Corporation
  Distributed under the terms of the BSD-3-Clause License
*/
Object.defineProperty(exports, "__esModule", { value: true });
var _1 = require(".");
var mode_1 = require("./mode");
function activate(app) {
    console.log(_1.PLUGIN_ID, app);
    mode_1.defineRobotMode();
}
/**
 * Initialization data for the jupyterlab_robotmode extension.
 */
var extension = {
    activate: activate,
    autoStart: true,
    id: _1.PLUGIN_ID
};
exports.default = extension;
