import { execFileSync } from "node:child_process";
import { readFileSync, statSync } from "node:fs";
import path from "node:path";
import MarkdownIt from "markdown-it";
import GithubSlugger from "github-slugger";

// Read the Git index so CI validates versioned documentation, including staged additions.
const root = execFileSync("git", ["rev-parse", "--show-toplevel"], { encoding: "utf8" }).trim();
const tracked = execFileSync("git", ["ls-files", "-z"], { cwd: root, encoding: "utf8" })
  .split("\0").filter(Boolean);
const trackedSet = new Set(tracked);
const markdown = tracked.filter((file) => file.endsWith(".md"));
const parser = new MarkdownIt();
const errors = [];
const documents = new Map();

for (const file of markdown) {
  try {
    const source = readFileSync(path.join(root, file), "utf8");
    const tokens = parser.parse(source, {});
    const slugger = new GithubSlugger();
    const anchors = new Set();
    tokens.forEach((token, index) => {
      if (token.type === "heading_open") {
        const inline = tokens[index + 1];
        const text = inline.children.filter((child) => ["text", "code_inline", "image"].includes(child.type))
          .map((child) => child.content).join("");
        anchors.add(slugger.slug(text));
      }
    });
    documents.set(file, { source, tokens, anchors });
  } catch (error) {
    errors.push(`${file}: ${error.message}`);
  }
}

// Parse Markdown links/images (including reference links), ignoring code fences.
let localLinks = 0;
function checkLink(file, href) {
  if (/^[a-z][a-z\d+.-]*:/i.test(href) || href.startsWith("//")) return;
  localLinks += 1;
  try {
    const [beforeFragment, fragment] = href.split("#", 2);
    const pathname = decodeURIComponent(beforeFragment.split("?", 1)[0]);
    const resolved = pathname
      ? pathname.startsWith("/")
        ? path.resolve(root, `.${pathname}`)
        : path.resolve(root, path.dirname(file), pathname)
      : path.join(root, file);
    const relative = path.relative(root, resolved).split(path.sep).join("/");
    if (relative.startsWith("../") || path.isAbsolute(relative)) throw new Error("target leaves repository");
    const stat = statSync(resolved);
    const versioned = stat.isDirectory()
      ? relative === "" || tracked.some((entry) => entry.startsWith(`${relative}/`))
      : trackedSet.has(relative);
    if (!versioned) throw new Error("target is not tracked by Git");
    if (fragment && documents.has(relative) && !documents.get(relative).anchors.has(decodeURIComponent(fragment))) {
      throw new Error(`heading #${fragment} does not exist`);
    }
  } catch (error) {
    errors.push(`${file}: ${href}: ${error.message}`);
  }
}
function visit(file, tokens) {
  for (const token of tokens) {
    if (token.type === "link_open") checkLink(file, token.attrGet("href"));
    if (token.type === "image") checkLink(file, token.attrGet("src"));
    if (token.children) visit(file, token.children);
  }
}
for (const [file, document] of documents) visit(file, document.tokens);

// The process document owns the tree; avoid a second architecture manifest.
const processFile = "doc/DEVELOPMENT_PROCESS.md";
const processDocument = documents.get(processFile);
const tree = processDocument?.tokens.find((token) => token.type === "fence" && token.info === "text"
  && token.content.startsWith("balance-budgeting/\n"));
let treeEntries = 0;
if (!tree) {
  errors.push(`${processFile}: missing repository tree`);
} else {
  const parents = [];
  for (const line of tree.content.trimEnd().split("\n").slice(1)) {
    const match = /^((?:│   |    )*)(?:├── |└── )([^\s]+)$/.exec(line);
    if (!match) {
      errors.push(`${processFile}: invalid tree line: ${line}`);
      continue;
    }
    const depth = match[1].length / 4;
    const name = match[2].replace(/\/$/, "");
    parents.length = depth;
    const entry = [...parents, name].join("/");
    treeEntries += 1;
    const directory = match[2].endsWith("/");
    if (directory) parents.push(name);
    try {
      const stat = statSync(path.join(root, entry));
      const versioned = directory
        ? tracked.some((file) => file.startsWith(`${entry}/`))
        : trackedSet.has(entry);
      if (stat.isDirectory() !== directory || !versioned) throw new Error("missing or not tracked");
    } catch (error) {
      errors.push(`${processFile}: tree entry ${entry}: ${error.message}`);
    }
  }
}

if (errors.length) {
  errors.forEach((error) => console.error(error));
  process.exitCode = 1;
} else {
  console.log(`Checked ${markdown.length} Markdown files, ${localLinks} local links, and ${treeEntries} repository tree entries.`);
}
