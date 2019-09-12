/*
  Copyright (c) 2018 Georgia Tech Research Corporation
  Distributed under the terms of the BSD-3-Clause License
*/

import { JupyterLab, JupyterFrontEndPlugin } from '@jupyterlab/application';

import { PLUGIN_ID } from '.';

import { defineRobotMode } from './mode';

function activate(app: JupyterLab) {
  console.log(PLUGIN_ID, app);
  defineRobotMode();
}

/**
 * Initialization data for the jupyterlab_robotmode extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  activate,
  autoStart: true,
  id: PLUGIN_ID
};

export default extension;
