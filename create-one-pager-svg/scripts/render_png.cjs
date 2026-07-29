#!/usr/bin/env node
/** SVGをSharpでPNGへ変換する。 */

const fs = require('fs');
const path = require('path');

function usage() {
  console.error('使用方法: node render_png.cjs 入力.svg 出力.png [--scale 2]');
}

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 2) {
    usage();
    process.exitCode = 2;
    return;
  }
  const input = path.resolve(args[0]);
  const output = path.resolve(args[1]);
  const scaleIndex = args.indexOf('--scale');
  const scale = scaleIndex >= 0 ? Number(args[scaleIndex + 1]) : 2;
  if (!Number.isFinite(scale) || scale <= 0 || scale > 4) {
    throw new Error('--scale は0より大きく4以下の数値にしてください。');
  }
  if (!fs.existsSync(input)) {
    throw new Error(`入力SVGが見つかりません: ${input}`);
  }

  let sharp;
  try {
    sharp = require('sharp');
  } catch (error) {
    throw new Error('sharpを読み込めません。npm install sharp を実行するか、NODE_PATHを設定してください。');
  }

  fs.mkdirSync(path.dirname(output), { recursive: true });
  const metadata = await sharp(input).metadata();
  const width = metadata.width ? Math.round(metadata.width * scale) : undefined;
  await sharp(input, { density: Math.round(96 * scale) })
    .resize(width ? { width } : undefined)
    .png({ compressionLevel: 9, adaptiveFiltering: true })
    .toFile(output);
  const rendered = await sharp(output).metadata();
  console.log(JSON.stringify({
    status: 'ok',
    input,
    output,
    width: rendered.width,
    height: rendered.height,
    scale,
  }, null, 2));
}

main().catch((error) => {
  console.error(JSON.stringify({ status: 'error', message: error.message }, null, 2));
  process.exitCode = 1;
});

