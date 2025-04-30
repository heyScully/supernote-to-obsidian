# supernote-to-obsidian

This script that takes a daily .note file, converts handwriting to markdown, and inserts it into today's Obsidian daily note.  

For me, I really like taking handwritten notes for recall and general presence.  I find my Supernote Manta is truly great for this.  No other e-ink tablet feels more like pen-on-pad to me.  The problem is that I need searchable notes, and my handwriting is awful (and I tend to write in all caps).  The on-device handwriting recognition may work for some people, but not for me.  I find that Gemini Pro 2.5 works really well for my handwriting, and using this script in my daily routine still keeps me in the free tier with Google.  Lots of room to improve, but here's a braindump of the things you may want to know to start.

The key is that my Manta is my input device, but not my retrieval device.  Notes on my tablet are ephemeral, but I save PDF versions in my Obsidian notebook like I might hang onto old notebooks.  Obsidian is my main (and searchable) note store.  However, I also sideloaded Obsidian on my Manta, so I have that option for retrieval on the tablet as well if my Manta is what is handy.

# What it does

Hazel looks for `.note` files in a Supernote directory created *before* today.  When it finds one, it triggers this script, which:
1. uses [supernote-tool](https://github.com/jya-dev/supernote-tool) to create a PDF
2. sends the PDF to Google Gemini for handwriting recognition, requesting clean markdown in response, preserving structures called out in the prompt *(I make a point ***not*** write anything confidential in my notes)*
3. looks to see if there's already an Obsidian daily note that matches the date in the filename of the Supernote file, and if not, creates one
4. inserts the markdown below the Supernote header in my Obsidian notes, saves the PDF in an `/attachments` subfolder, and includes the handwritten PDF below the markdown for reference
5. moves the original `.note` file to a `/processed_notes` subdirectory from its original location *(I may batch delete them at some point.)*

# My setup and work flow

On my Supernote, I create a new .note file for each day, accepting the default file name.  For work notes, I create the note in the /Document folder.  For personal notes, I create a note in the /Notes folder.  I use Dropbox to sync device content to my laptop.

I maintain two Obsidian vaults, one personal and one for work.  In each vault, I have a `/Daily Notes` folder with subdirectories in the format `YYYY/MM-MMM/YYYY-MM-DD ddd`. The Daily Notes core plugin works well for this, especially when combined with the Calendar community plugins.  At the bottom of my Daily Note template, I have a section with the following heading in each: `## ✨ Supernote`.  Each month folder has an `/attachments` folder where PDFs are kept.

I run Hazel on my Macbook to monitor the Supernote Documents and Notes folders for changes.  More specifically, I have a rule that looks for `.note` files with a file name that starts with 8 digits.  Since I only want to process notes from yesterday (or earlier), I also condition the rule on passing the following Applescript:
```applescript
tell application "Finder"
	set fileName to name of theFile
	set fileDate to text 1 thru 8 of fileName
	
	-- Get today's date in YYYYMMDD format
	set todayDateCmd to "date +%Y%m%d"
	set todayDate to do shell script todayDateCmd
	
	-- Compare and return true if file date is before today
	return fileDate < todayDate
end tell
```
When a match is detected, a shell script is run, which passes **$1** to this python script.  

***caveat: 
Due to some of the quirks of Dropbox, I find that the file needs to change at a time when it matches.  That is, yesterday's note won't be recognized (it hasn't actually been downloaded as much as just listed in the directory), so it won't trigger the script.  The easiest way to work around this is to sync Dropbox manually the next morning.  You can also open yesterday's note, make a mark on the page, and resync Dropbox manually if you had already done it the prior day.  Worst case, it will catch up after you sync your next day's note, triggering Hazel to look at the files in the directory again.***

# Setting up the Script

1. clone the repo
2. get yourself a Google API Key for Gemini if you don't already have one
3. store your Gemini API key in: gemini api key in ~/.api_keys/gemini_key
4. create a .env file in your repo and populate:
```python
# obsidian folders
OBSIDIAN_DIR = "" # daily notes directory
SUPERNOTE_TOOL_PATH = ""  # something like /Users/[username]/Library/Python/3.9/bin
```
5. you'll probably want to add that .env to a .gitignore in the same folder just to be safe

# Some cool things
*You can see some useful callouts in the Gemini prompt.*
* writing AI in a circle to the left of a line item -- my shorthand for Action Item -- will convert it to a markdown task. In Obsidian, I additionally use the Tasks community plug-in, combined with the Homepage community plug-in, to keep a running aggregation of all my open and recently closed tasks across all notes.
* ALL CAPS handwriting is converted to normal capitalization
* It recognizes text highlighted with the highlighter pen on my Manta and preserves the highlighting in markdown
* Underlined text on its own line is treated like an H3 heading
* and a few other callouts to preserve as much formatting from the original as possible in markdown
