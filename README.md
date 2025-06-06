# WMATA Pass Analyzer

This tool helps you analyze your WMATA Metro Pass usage by comparing your card usage data against fare data to determine the best pass for your travel patterns or determine if you saved money with your current pass.

## Developing

Install dependencies with `npm install` (or `pnpm install` or `yarn`), start a development server:

```bash
npm run dev

# or start the server and open the app in a new browser tab
npm run dev -- --open
```

## Building

To create a production version of the app:

```bash
npm run build
```

You can preview the production build with `npm run preview`.

To deploy to cPanel, run:

```bash
npm run build:cpanel
```

This will create a `to_upload.tar` that you can upload to your cPanel account and then extract it to your Node.js application directory. Set the startup file to `index.cjs` in your cPanel Node.js application settings.
