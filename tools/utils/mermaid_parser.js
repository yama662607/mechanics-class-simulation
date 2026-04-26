const { JSDOM } = require("jsdom");
const createDOMPurify = require("dompurify");

// 1. Setup virtual browser environment
const dom = new JSDOM('<!DOCTYPE html><html><body><div id="graph"></div></body></html>');
global.window = dom.window;
global.document = dom.window.document;
global.navigator = dom.window.navigator;

// 2. Setup DOMPurify
const DOMPurify = createDOMPurify(dom.window);
global.DOMPurify = DOMPurify;

// 3. Load Mermaid
// mermaid v10+ is ESM only usually, but some CJS builds exist.
const mermaidPkg = require("mermaid");
const mermaid = mermaidPkg.default || mermaidPkg;

// 4. Initialize Mermaid
if (typeof mermaid.initialize === 'function') {
    mermaid.initialize({
        startOnLoad: false,
        suppressErrorOutput: true,
    });
}

// 5. Read input from stdin
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
                    message: msg
                });
            }
        }

        console.log(JSON.stringify({ results }));
        process.exit(0);
    } catch (e) {
        console.error("Fatal error in Node.js validator:", e);
        process.exit(1);
    }
});
