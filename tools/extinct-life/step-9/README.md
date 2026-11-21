# Atlantic Tracks — YouTube cover and title

**Launch title:** Why Are These Dinosaur Footprints an Ocean Apart?  
**Cover copy:** `6,000 KM APART`

For the [Cinema Edition](../step-8/README.md), not an alternate cut. The title asks why the two sites are separated; the cover gives the visual clue and the approximate modern regional distance. The two impressions and the ocean are original illustrative artwork, not photographs of either fossil site or evidence of the same dinosaur.

The design follows the [Batch 01 packaging study](../step-1/Extinct-Life-Batch-01-Market-Research.md#3-what-to-use-for-extinct-life): one readable clue, short type, and a title that adds context rather than repeating the number. The selected art keeps both impressions clear of the headline and the lower-right runtime badge. Inspect the exported JPEG at 480, 320, 176 and 120 pixels wide with the QA badge; the badge is not baked into the upload file. These are legibility checks, not audience testing or a view prediction.

## Rebuild

Use Python 3.11+, Pillow 11.3.0, the selected `Atlantic-Tracks-Selected-Art.png`, and the same checksum-pinned Space Grotesk variable font as the [Monarch Cam builder](../../monarch-ant-v3/packaging/README.md). Keep both art and font outside Git. From the repository root:

```sh
python3 tools/extinct-life/step-9/build_cover.py --art path/to/Atlantic-Tracks-Selected-Art.png --font path/to/SpaceGrotesk.ttf
```

Exports `Atlantic-Tracks-YouTube-Thumbnail.jpg` (1920 × 1080, sRGB, under 2 MB) and `Atlantic-Tracks-YouTube-Title.txt` to `deliverables/extinct-life-step-9/`. The encoded feed checks and the checksum receipt are in `.cache/atlantic-cover/qa/`. The builder does not change the film, publish it, or change permissions.
