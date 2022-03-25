declare module '*?raw' {
  const res: string;
  export default res;
}

declare module '!!file-loader*' {
  const res: string;
  export default res;
}

declare let indexURL: string;
declare let _pipliteWheelUrl: any;
declare let _pipliteUrls: string[];
declare let _disablePyPIFallback: boolean;
declare let loadPyodide: any;
