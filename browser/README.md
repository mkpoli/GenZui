# Historical kana in Windows browsers

Install GenSeki Hentaigana Gothic Regular and Bold from the
[official release](https://github.com/MihailJP/GenSekiHentaiganaGothic/releases).
Version 1.201 covers the project's 309-character inventory, including all 286
hentaigana and the seven Unicode 18 kana additions.

Installing a font does not establish a universal fallback order. Applications
choose their fallback fonts. Windows' `FontLink\SystemLink` registry mechanism
is for GDI; it does not provide a general configuration for modern browsers.
See [Microsoft's font fallback documentation](https://learn.microsoft.com/en-us/globalization/fonts-layout/fonts).

## Firefox

Firefox accepts comma-separated fallback lists in `about:config`. Append
`GenSeki Hentaigana Gothic` to the existing values for:

```text
font.name-list.serif.ja
font.name-list.sans-serif.ja
font.name-list.monospace.ja
font.name-list.serif.x-unicode
font.name-list.sans-serif.x-unicode
font.name-list.monospace.x-unicode
```

For an absent string preference, create it with the font family as its value.
Retain existing names and their order. The `ja` entries cover Japanese text;
`x-unicode` supplies a fallback for characters whose script is not recognized by
the browser's Unicode data. Fully exit and reopen Firefox after installing fonts.
The same preferences can be placed in the profile's `user.js` to apply on startup.

## Chrome and Vivaldi

Use `historical-kana-fallback.user.js` with
[Tampermonkey](https://www.tampermonkey.net/index.php?browser=chrome).

1. Open Tampermonkey's **Create a new script** editor.
2. Replace the template with the entire userscript, then save with **Ctrl+S**.
3. Open Tampermonkey's extension details and enable **Allow User Scripts**
   (**ユーザースクリプトを許可**). Check this even when the extension and script
   are already enabled. Permit site access for the pages where it should run.
4. Reload the affected web pages. Tampermonkey's popup should list the script
   as running on the page.

A red × on Tampermonkey with a “some URLs are restricted” tooltip indicates
an execution restriction. If **Allow User Scripts** is already on, toggle it
off and on again, then reload. See the
[execution-permission instructions](https://www.tampermonkey.net/faq.php?locale=en&q=Q209)
and the [matching Vivaldi report](https://github.com/Tampermonkey/tampermonkey/issues/2844).
The local setup page's **Preview kana fallback** button runs a standalone test;
its success does not establish that Tampermonkey can execute on websites.

The script appends a local font face to text elements containing historical kana.
Its Unicode ranges restrict that face to historical kana and their combining
marks. Fonts already named by the page retain priority. Ordinary text continues
to use the page's existing font stack. Newly inserted text and input values are
handled as well. Password inputs are excluded.

The script makes no network requests. It runs on HTTP and HTTPS pages and uses
the installed Regular and Bold fonts. It does not affect browser interface pages,
PDF viewers, canvas text, or text inside shadow roots. A site's own style updates
can require a reload. Disable the script for a site through Tampermonkey if needed.

For a site under your control, an explicit CSS stack is simpler:

```css
.historical-kana {
  font-family: "Noto Sans JP", "GenSeki Hentaigana Gothic", sans-serif;
}
```

The userscript uses the project's MIT licence. Font licences remain with their
respective upstream projects.

## Windows Terminal, Codex and Herdr

Windows Terminal 1.21 and later accepts a comma-separated font fallback list.
Append `GenSeki Hentaigana Gothic` to the existing `profiles.defaults.font.face`
value in Windows Terminal's JSON settings. For example:

```json
"font": {
  "face": "FiraCode Nerd Font Mono, GenSeki Hentaigana Gothic"
}
```

Profiles with their own `font.face` override need the same addition. Existing
profiles inherit the default when they have no override. If the font change does
not appear in an existing window, open a new terminal window. The font must be
installed in Windows; installing it only in WSL does not supply it to the Windows
renderer. Herdr and Codex pass Unicode text to that renderer.

Reference: [Microsoft's font fallback announcement](https://devblogs.microsoft.com/commandline/windows-terminal-preview-1-21-release/#font-fallback).
