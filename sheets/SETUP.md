# Google Sheets backend — setup

One-time, about five minutes, done from your Google account (I can't do this part).
When you're finished, send back the **Web App URL** from step 5.

## 1. Make the sheet

Go to [sheets.new](https://sheets.new). Name it something like `944 FMEA data`.
Leave it blank — the script builds the tabs.

## 2. Paste the script

In the sheet: **Extensions → Apps Script**. Delete whatever's in the editor, paste the
entire contents of `Code.gs` from this folder, and save (⌘S). Name the project anything.

## 3. Run `setup()` once

In the editor toolbar, pick `setup` from the function dropdown and press **Run**.
It will ask you to authorize the script for this sheet — approve it (you'll get a
"Google hasn't verified this app" warning because it's your own script; click
Advanced → Go to project). Switch back to the sheet: you should now see four tabs —
`ScoreChanges`, `Sessions`, `Comments`, `BuildTasks` — each with a bold header row.

## 4. Deploy as a web app

Back in the editor: **Deploy → New deployment**. Click the gear next to "Select type"
and choose **Web app**. Set:

- Description: anything
- Execute as: **Me**
- Who has access: **Anyone**

Click **Deploy**. Authorize again if asked.

"Anyone" is what lets the dashboard post to it without visitors signing in. The URL is
unguessable and the script only ever appends rows — it can't read anything else in
your account or delete data.

## 5. Copy the URL

Copy the **Web app URL** (looks like `https://script.google.com/macros/s/AKfy.../exec`)
and send it to me. That URL is the only thing the dashboard needs.

## Verify (optional)

Paste `<your URL>?sheet=Comments` into a browser. You should see `{"rows":[]}`.

## Later changes

If you ever edit `Code.gs`, you must **Deploy → Manage deployments → edit → New version**
— saving alone doesn't update the live URL. The URL stays the same across versions.
