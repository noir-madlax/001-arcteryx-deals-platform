#!/usr/bin/env node
/** Audit Arc'teryx rows while enforcing the shared GearDrop brand contract. */
import fs from 'node:fs';
import process from 'node:process';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const {
  extractModelFamily,
  isArcTeryxProduct,
  standardProductName,
} = require(path.join(ROOT, 'arcteryx-names.js'));
const {
  isSupportedBrandProduct,
  productBrand,
} = require(path.join(ROOT, 'gear-brands.js'));

const DISCRIMINATOR = /\b(?:[A-Za-z]*\d+[A-Za-z]*|LiTRIC|SuperLight|StormHood|DownWord|GTX|SV|AR|LT|SL|FL|MX|LD|SS|LS)\b/gi;

function expectedGender(row, raw) {
  if (/\b(?:women(?:[’']?s)?|woman|damen|femme)\b/i.test(raw)) return "Women's";
  if (/\b(?:men(?:[’']?s)?|man|herren|homme)\b/i.test(raw)) return "Men's";
  if (/\bunisex\b/i.test(raw)) return 'Unisex';
  const key = String(row.gender || '').toLowerCase();
  if (key === 'women') return "Women's";
  if (key === 'men') return "Men's";
  if (key === 'unisex') return 'Unisex';
  return '';
}

function unique(values) {
  return [...new Set(values)];
}

export function auditRows(inputRows, options = {}) {
  const activeRows = inputRows.filter((row) => (row.status || 'active') === 'active');
  const rejectedRows = activeRows.filter((row) => !isSupportedBrandProduct(row));
  const supportedRows = activeRows.filter(isSupportedBrandProduct);
  const acceptedRows = supportedRows.filter((row) => productBrand(row) === 'arcteryx' && isArcTeryxProduct(row));
  const supportedNonArcRows = supportedRows.filter((row) => productBrand(row) !== 'arcteryx');
  const blankNames = [];
  const unknownFamilies = [];
  const lostDiscriminators = [];
  const genderMismatches = [];
  const canonicalRows = [];

  for (const row of acceptedRows) {
    const raw = String(row.full_name || row.model || '').trim();
    const standard = standardProductName(raw, row);
    const family = extractModelFamily(standard);
    canonicalRows.push({ row, raw, standard, family });
    if (!standard) blankNames.push(row);
    if (standard && !family) unknownFamilies.push({ row, raw, standard });

    const missing = unique(raw.match(DISCRIMINATOR) || [])
      .filter((token) => !new RegExp(`\\b${token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i').test(standard));
    if (missing.length) lostDiscriminators.push({ row, raw, standard, missing });

    const gender = expectedGender(row, raw);
    if (gender && !standard.endsWith(` ${gender}`)) {
      genderMismatches.push({ row, raw, standard, expected: gender });
    }
  }

  const byCanonical = new Map();
  for (const item of canonicalRows) {
    const key = `${item.row.dealer || 'unknown'}\u0000${item.standard.toLowerCase()}`;
    const values = byCanonical.get(key) || [];
    values.push(item);
    byCanonical.set(key, values);
  }
  const canonicalGroupsWithMultipleUrls = [...byCanonical.values()]
    .filter((items) => unique(items.map((item) => item.row.url)).length > 1).length;

  const violations = blankNames.length + unknownFamilies.length + lostDiscriminators.length + genderMismatches.length
    + (options.strictSource ? rejectedRows.length : 0);

  return {
    active: activeRows.length,
    accepted: acceptedRows.length,
    supportedNonArc: supportedNonArcRows.length,
    rejected: rejectedRows.length,
    uniqueStandardNames: unique(canonicalRows.map((item) => item.standard)).length,
    canonicalGroupsWithMultipleUrls,
    blankNames,
    unknownFamilies,
    lostDiscriminators,
    genderMismatches,
    rejectedRows,
    violations,
  };
}

function parseArgs(argv) {
  const args = { online: false, file: '', strictSource: false, json: false };
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === '--online') args.online = true;
    else if (value === '--strict-source') args.strictSource = true;
    else if (value === '--json') args.json = true;
    else if (value === '--file') args.file = argv[++index] || '';
    else throw new Error(`unknown argument: ${value}`);
  }
  if (Number(args.online) + Number(Boolean(args.file)) !== 1) {
    throw new Error('choose exactly one source: --online or --file PATH');
  }
  return args;
}

export function publicCatalogConfig(root = ROOT) {
  for (const filename of ['index.html', 'product-detail.html']) {
    const configPath = path.join(root, filename);
    if (!fs.existsSync(configPath)) continue;
    const source = fs.readFileSync(configPath, 'utf8');
    const url = source.match(/const SUPABASE_URL\s*=\s*'([^']+)'/)?.[1];
    const anon = source.match(/const SUPABASE_ANON\s*=\s*'([^']+)'/)?.[1];
    if (url && anon) return { url, anon };
  }
  throw new Error('public catalog config not found');
}

async function fetchOnlineRows() {
  const { url, anon } = publicCatalogConfig();
  const rows = [];
  const select = 'sku_id,dealer,brand,model,full_name,url,gender,status';
  for (let from = 0; ; from += 1000) {
    const query = new URLSearchParams({ select, status: 'eq.active', order: 'sku_id.asc' });
    const response = await fetch(`${url}/rest/v1/products?${query}`, {
      headers: { apikey: anon, Authorization: `Bearer ${anon}`, Range: `${from}-${from + 999}` },
    });
    if (!response.ok) throw new Error(`catalog HTTP ${response.status}`);
    const page = await response.json();
    rows.push(...page);
    if (page.length < 1000) break;
  }
  return rows;
}

function readRows(file) {
  const payload = JSON.parse(fs.readFileSync(file, 'utf8'));
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload.products)) return payload.products;
  throw new Error('file must contain an array or {"products": [...]}');
}

function compactSamples(items, mapper) {
  return items.slice(0, 5).map(mapper);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const rows = args.online ? await fetchOnlineRows() : readRows(args.file);
  const result = auditRows(rows, { strictSource: args.strictSource });
  const report = {
    active: result.active,
    accepted: result.accepted,
    supportedNonArc: result.supportedNonArc,
    rejected: result.rejected,
    uniqueStandardNames: result.uniqueStandardNames,
    canonicalGroupsWithMultipleUrls: result.canonicalGroupsWithMultipleUrls,
    blankNames: result.blankNames.length,
    unknownFamilies: result.unknownFamilies.length,
    lostDiscriminators: result.lostDiscriminators.length,
    genderMismatches: result.genderMismatches.length,
    strictSource: args.strictSource,
    violations: result.violations,
    samples: {
      rejected: compactSamples(result.rejectedRows, (row) => ({ dealer: row.dealer, name: row.full_name || row.model, url: row.url })),
      unknownFamilies: compactSamples(result.unknownFamilies, (item) => ({ name: item.standard, url: item.row.url })),
      lostDiscriminators: compactSamples(result.lostDiscriminators, (item) => ({ name: item.standard, missing: item.missing, url: item.row.url })),
      genderMismatches: compactSamples(result.genderMismatches, (item) => ({ name: item.standard, expected: item.expected, url: item.row.url })),
    },
  };

  if (args.json) console.log(JSON.stringify(report, null, 2));
  else {
    console.log(`[names] active=${report.active} arc_audited=${report.accepted} supported_non_arc=${report.supportedNonArc} rejected=${report.rejected}`);
    console.log(`[names] unique=${report.uniqueStandardNames} multi_url_groups=${report.canonicalGroupsWithMultipleUrls}`);
    console.log(`[names] blank=${report.blankNames} unknown_family=${report.unknownFamilies} lost_tokens=${report.lostDiscriminators} gender_mismatch=${report.genderMismatches}`);
    if (report.rejected) console.log(`[names] source_rejections=${JSON.stringify(report.samples.rejected)}`);
    if (report.unknownFamilies) console.log(`[names] unknown_families=${JSON.stringify(report.samples.unknownFamilies)}`);
    if (report.lostDiscriminators) console.log(`[names] lost_discriminators=${JSON.stringify(report.samples.lostDiscriminators)}`);
    if (report.genderMismatches) console.log(`[names] gender_mismatches=${JSON.stringify(report.samples.genderMismatches)}`);
    console.log(report.violations ? '[names] FAIL' : '[names] OK');
  }
  process.exitCode = report.violations ? 1 : 0;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.error(`[names] ERROR ${error.message}`);
    process.exitCode = 1;
  });
}
