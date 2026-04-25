const { JSDOM } = require("jsdom");
const createDOMPurify = require("dompurify");

const dom = new JSDOM("<!DOCTYPE html><html><body><div id=\"graph\"></div></body></html>");
global.window = dom.window;
global.document = dom.window.document;
global.navigator = dom.window.navigator;
global.DOMPurify = createDOMPurify(dom.window);

const mermaidPkg = require("mermaid");
const mermaid = mermaidPkg.default || mermaidPkg;

if (typeof mermaid.initialize === "function") {
  mermaid.initialize({
    startOnLoad: false,
    suppressErrorOutput: true,
  });
}

let inputData = "";

process.stdin.on("data", (chunk) => {
  inputData += chunk;
});

process.stdin.on("end", async () => {
  if (!inputData.trim()) {
    process.exit(0);
  }

  try {
    const payload = JSON.parse(inputData);
    const results = [];

    for (const block of payload.blocks) {
      try {
        await mermaid.parse(block.code);
        results.push({ valid: true, file: block.file, line: block.line });
      } catch (err) {
        const msg = err.str || err.message || err.toString();
        results.push({
          valid: false,
          file: block.file,
          line: block.line,
          message: msg,
        });
      }
    }

    console.log(JSON.stringify({ results }));
    process.exit(0);
  } catch (err) {
    console.error("Fatal error in Mermaid validator:", err);
    process.exit(1);
  }
});
