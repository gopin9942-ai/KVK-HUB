import { GtcrnProcessor, loadGtcrnModule } from "https://esm.sh/@sapphi-red/gtcrn-wasm@0.0.3?bundle";

const WASM_URL = "https://cdn.jsdelivr.net/npm/@sapphi-red/gtcrn-wasm@0.0.3/dist/gtcrn.wasm";
const FRAME_SIZE = 768; // GTCRN 48 kHz mono frame
const QUANTUM = 128;
const BLOCKS_PER_FRAME = FRAME_SIZE / QUANTUM;

class KVKGTCRNDenoiser extends AudioWorkletProcessor {
  constructor() {
    super();
    this.processor = null;
    this.ready = false;
    this.destroyed = false;
    this.inputFrame = new Float32Array(FRAME_SIZE);
    this.outputFrame = new Float32Array(FRAME_SIZE);
    this.inputPhase = 0;
    this.outputPhase = BLOCKS_PER_FRAME - 1;

    this.port.onmessage = (event) => {
      if (event.data?.type === "destroy") this.destroy();
    };

    this.initialize();
  }

  async initialize() {
    try {
      const response = await fetch(WASM_URL);
      if (!response.ok) throw new Error("GTCRN model download failed: " + response.status);
      const wasmBinary = await response.arrayBuffer();
      const module = await loadGtcrnModule({ wasmBinary });
      if (this.destroyed) return;
      this.processor = new GtcrnProcessor(module, { sampleRate: 48000 });
      this.ready = true;
      this.port.postMessage({ type: "ready" });
    } catch (error) {
      this.port.postMessage({ type: "error", message: error?.message || String(error) });
    }
  }

  process(inputs, outputs) {
    const output = outputs[0]?.[0];
    if (!output) return true;
    output.fill(0);

    if (this.destroyed) return false;
    const input = inputs[0]?.[0];
    if (!this.ready || !input || input.length !== QUANTUM) return true;

    this.inputFrame.set(input, this.inputPhase * QUANTUM);

    if (this.inputPhase === BLOCKS_PER_FRAME - 1) {
      this.outputFrame.set(this.processor.process(this.inputFrame));
      output.set(this.outputFrame.subarray(0, QUANTUM));
      this.outputPhase = 1 % BLOCKS_PER_FRAME;
    } else {
      const start = this.outputPhase * QUANTUM;
      output.set(this.outputFrame.subarray(start, start + QUANTUM));
      this.outputPhase = (this.outputPhase + 1) % BLOCKS_PER_FRAME;
    }

    this.inputPhase = (this.inputPhase + 1) % BLOCKS_PER_FRAME;
    return true;
  }

  destroy() {
    this.destroyed = true;
    this.processor?.destroy();
    this.processor = null;
  }
}

registerProcessor("kvk-gtcrn-denoiser", KVKGTCRNDenoiser);
