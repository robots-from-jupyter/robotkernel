// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import { PageConfig, URLExt } from '@jupyterlab/coreutils';

import { JupyterLiteServer, JupyterLiteServerPlugin } from '@jupyterlite/server';

import { IKernel, IKernelSpecs } from '@jupyterlite/kernel';

import * as kernelIcon from '!!file-loader!../style/robotframework.png';

/**
 * The default CDN fallback for Pyodide
 */
const PYODIDE_CDN_URL = 'https://cdn.jsdelivr.net/pyodide/v0.19.1/full/pyodide.js';

/**
 * The id for the extension, and key in the litePlugins.
 */
const PLUGIN_ID = '@jupyterlite/robolite-kernel-extension:kernel';

/**
 * A plugin to register the Pyodide kernel.
 */
const kernel: JupyterLiteServerPlugin<void> = {
  id: PLUGIN_ID,
  autoStart: true,
  requires: [IKernelSpecs],
  activate: (app: JupyterLiteServer, kernelspecs: IKernelSpecs) => {
    const config =
      JSON.parse(PageConfig.getOption('litePluginSettings') || '{}')[PLUGIN_ID] || {};
    const url = config.pyodideUrl || PYODIDE_CDN_URL;
    const pyodideUrl = URLExt.parse(url).href;
    const rawPipUrls = config.pipliteUrls || [];
    const pipliteUrls = rawPipUrls.map((pipUrl: string) => URLExt.parse(pipUrl).href);
    const disablePyPIFallback = !!config.disablePyPIFallback;

    kernelspecs.register({
      spec: {
        name: 'Robot Framework',
        display_name: 'Robot Framework',
        language: 'robotframework',
        argv: [],
        spec: {
          argv: [],
          env: {},
          display_name: 'Robot Framework',
          language: 'robotframework',
          interrupt_mode: 'message',
          metadata: {},
        },
        resources: {
          'logo-64x64': kernelIcon.default
        },
      },
      create: async (options: IKernel.IOptions): Promise<IKernel> => {
        const { RoboliteKernel } = await import('@jupyterlite/robolite-kernel');

        return new RoboliteKernel({
          ...options,
          pyodideUrl,
          pipliteUrls,
          disablePyPIFallback,
        });
      },
    });
  },
};

const plugins: JupyterLiteServerPlugin<any>[] = [kernel];

export default plugins;
