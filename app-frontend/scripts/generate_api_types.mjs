import fs from "node:fs";
import path from "node:path";

const rootDir = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const openapiPath = path.resolve(rootDir, "../app-backend/openapi.json");
const outputPath = path.resolve(rootDir, "src/lib/api-types.ts");

const primitiveMap = {
  string: "string",
  integer: "number",
  number: "number",
  boolean: "boolean",
};

function toType(schema) {
  if (!schema) return "unknown";
  if (schema.$ref) {
    return schema.$ref.split("/").pop();
  }
  if (schema.oneOf) {
    return schema.oneOf.map((item) => toType(item)).join(" | ");
  }
  if (schema.anyOf) {
    return schema.anyOf.map((item) => toType(item)).join(" | ");
  }
  if (schema.allOf) {
    return schema.allOf.map((item) => toType(item)).join(" & ");
  }
  if (schema.type === "array") {
    return `${toType(schema.items)}[]`;
  }
  if (schema.type === "object" || schema.properties || schema.additionalProperties) {
    const props = schema.properties || {};
    const required = new Set(schema.required || []);
    const lines = Object.entries(props).map(([key, value]) => {
      const optional = required.has(key) ? "" : "?";
      return `  ${JSON.stringify(key)}${optional}: ${toType(value)};`;
    });
    if (schema.additionalProperties) {
      lines.push(`  [key: string]: ${toType(schema.additionalProperties)};`);
    }
    return `{\n${lines.join("\n")}\n}`;
  }
  if (schema.enum) {
    return schema.enum.map((value) => JSON.stringify(value)).join(" | ");
  }
  if (schema.type && primitiveMap[schema.type]) {
    return primitiveMap[schema.type];
  }
  return "unknown";
}

function generate() {
  if (!fs.existsSync(openapiPath)) {
    throw new Error(`OpenAPI schema not found: ${openapiPath}`);
  }
  const openapi = JSON.parse(fs.readFileSync(openapiPath, "utf-8"));
  const schemas = openapi?.components?.schemas || {};
  const typeBlocks = Object.entries(schemas).map(([name, schema]) => {
    return `export type ${name} = ${toType(schema)};\n`;
  });

  const content = `/* eslint-disable */\n/* AUTO-GENERATED FILE. DO NOT EDIT. */\n` +
    `/* Generated from app-backend/openapi.json */\n\n` +
    typeBlocks.join("\n");
  fs.writeFileSync(outputPath, content, "utf-8");
  console.log(`Generated API types: ${outputPath}`);
}

generate();
