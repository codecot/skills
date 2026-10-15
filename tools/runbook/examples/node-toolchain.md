# Preflight: a JavaScript toolchain

Read-only. The checks use `node` itself where a shell one-liner would be
clumsier, so this doubles as an example of `node` blocks. Run `status`, then
`render` to get the page.

```ask
MIN_NODE | Lowest Node major you accept | default=20
```

## Node is installed {#node critical}

Everything below needs it, so this is a gate.

```check
command -v node >/dev/null
```

## Node is recent enough {#node-major needs=node}

A `node` block runs with `node -e`; environment variables arrive as usual.

```check node
const major = Number(process.version.slice(1).split(".")[0]);
if (major < Number(process.env.MIN_NODE)) {
  console.error(`node ${process.version} is below ${process.env.MIN_NODE}`);
  process.exit(1);
}
```

## npm can reach its registry {#registry needs=node}

```check timeout=20
npm ping >/dev/null 2>&1
```

## A package.json exists here {#manifest needs=node}

```check node
const fs = require("fs");
if (!fs.existsSync("package.json")) process.exit(1);
JSON.parse(fs.readFileSync("package.json", "utf8"));
```

```do node
require("fs").writeFileSync("package.json", JSON.stringify({ name: "scratch", private: true }, null, 2) + "\n");
```

```undo
rm -f package.json
```
