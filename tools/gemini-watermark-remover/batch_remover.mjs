import fs from 'node:fs';
import { readFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import sharp from 'sharp';
import { removeWatermarkFromFile, inferMimeTypeFromPath } from './src/sdk/node.js';

// High performance Sharp codec
const sharpCodec = {
  async decodeImageData(buffer) {
    const { data, info } = await sharp(buffer).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
    return {
      width: info.width,
      height: info.height,
      data: Uint8ClampedArray.from(data)
    };
  },
  async encodeImageData(imageData, context = {}) {
    const filePath = context.filePath || '';
    const ext = path.extname(filePath).toLowerCase();
    let encoder = sharp(Buffer.from(imageData.data), {
      raw: {
        width: imageData.width,
        height: imageData.height,
        channels: 4
      }
    });
    if (ext === '.jpg' || ext === '.jpeg') {
      encoder = encoder.jpeg({ quality: 95 });
    } else if (ext === '.webp') {
      encoder = encoder.webp({ quality: 95 });
    } else {
      encoder = encoder.png();
    }
    return encoder.toBuffer();
  }
};

async function processTask(task, index, total, overwrite = false) {
  const { input, output } = task;
  const shouldOverwrite = overwrite || task.overwrite === true;
  try {
    if (!shouldOverwrite && fs.existsSync(output) && fs.statSync(output).size > 0) {
      return { ok: true, input, output, cached: true };
    }
    await mkdir(path.dirname(output), { recursive: true });
    await removeWatermarkFromFile(input, {
      outputPath: output,
      mimeType: inferMimeTypeFromPath(output),
      decodeImageData: sharpCodec.decodeImageData,
      encodeImageData: sharpCodec.encodeImageData
    });
    console.log(`[PROGRESS] ${index + 1}/${total} ${path.basename(output)}`);
    return { ok: true, input, output, cached: false };
  } catch (err) {
    console.error(`[ERROR] ${input}: ${err.message}`);
    // If removal fails, copy original image as fallback so pipeline continues
    try {
      await fs.promises.copyFile(input, output);
    } catch (_) {}
    return { ok: false, input, output, error: err.message };
  }
}

async function runPool(tasks, concurrency = 6, overwrite = false) {
  let currentIndex = 0;
  const total = tasks.length;
  const results = [];

  async function worker() {
    while (currentIndex < total) {
      const idx = currentIndex++;
      const res = await processTask(tasks[idx], idx, total, overwrite);
      results[idx] = res;
    }
  }

  const workers = Array.from({ length: Math.min(concurrency, total) }, () => worker());
  await Promise.all(workers);
  return results;
}

async function main() {
  const args = process.argv.slice(2);
  const overwrite = args.includes('--overwrite');
  const filteredArgs = args.filter(a => a !== '--overwrite');

  if (filteredArgs[0] === '--single') {
    const input = filteredArgs[1];
    const output = filteredArgs[2];
    await processTask({ input, output, overwrite }, 0, 1, overwrite);
    return;
  }

  if (filteredArgs[0] === '--batch') {
    const jsonPath = filteredArgs[1];
    const content = await readFile(jsonPath, 'utf8');
    const tasks = JSON.parse(content);
    await runPool(tasks, 6, overwrite);
    return;
  }

  console.log('Usage: node batch_remover.mjs [--overwrite] --single <input> <output> OR node batch_remover.mjs [--overwrite] --batch <tasks.json>');
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
