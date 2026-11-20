"""Original score arrangement for V2, rendered from the credited FluidR3 bank.

This is a written score (harmonies, attack times, dynamics), not loops or
unaltered library music. Times in each movement are relative to its film edit.
"""
# Start relative to chapter, low sustained voicing, soft upper melodic gestures.
# In the continuous texture the marked events are revealed *between* sentences.
MOVEMENTS=[
 # Thin sand. Let grains introduce the sound before the first felt chord.
 [(0.05,'D3 A3','D4 .73;A3 2.09;E4 3.52'),(4.46,'Bb2 F3','F4 .64;D4 2.46'),
  (9.72,'G3 D4','C4 .29;A3 1.67'),(13.05,'A2 E3','D4 .42'),
  (16.02,'D3 A3 F4','A4 .47;F4 1.82;E4 2.71'),(20.43,'F3 C4','G4 .27;A4 1.58')],
 # The funnel: a gently descending phrase; local plucks follow the moving bank.
 [(0.,'D3 A3','D4 .41;C4 1.87;A3 3.00'),(5.28,'F3 C4','G4 .81;F4 2.53'),
  (11.06,'Bb2 F3','C4 .64;D4 2.83'),(16.38,'G3 D4','A3 .44;D4 2.58;p:G3 3.88'),
  (22.14,'D3 A3','A3 .64;p:F3 1.46;F4 3.73'),(27.68,'C3 G3','G4 .57;E4 2.22'),
  (32.77,'Bb2 F3','F4 .22;C4 2.95;p:Bb3 4.31'),(38.87,'G3 Bb3','D4 .74;C4 2.47'),
  (43.89,'A2 E3','A3 .41;E4 2.04')],
 # Stored tension: long-held fifths with a light upper voice, no ticking bed.
 [(0.,'D3 F3','A3 .36;D4 2.13'),(5.83,'A2 E3','B3 .56;D4 3.22'),
  (11.23,'A3 E4','G4 .28;F4 2.85'),(16.58,'Bb2 F3','D4 .46;A3 2.96'),
  (22.03,'G3 D4','C4 .17;D4 2.22'),(27.54,'E3 Bb3','E4 .36;G4 2.78'),
  (32.91,'A2 E3','D4 .26;Db4 3.06'),(38.06,'D3 A3','F4 .66;E4 2.94'),
  (44.21,'F3 C4','A3 .53;G4 2.52')],
 # The push. Bed recedes for unsupported snap and at the grain impact.
 [(0.,'G3 D4','Bb3 .38;D4 2.42'),(5.91,'Bb2 F3','F4 .52;D4 3.17'),
  (11.19,'A2 E3','E4 .21;D4 2.41'),(16.91,'D3 A3','A3 .66'),
  (22.42,'D3 F3','F4 .79'),(27.53,'Bb2 F3','C4 .39;D4 2.53'),
  (32.70,'F3 C4','G4 .31;A4 2.13;E4 3.82'),(38.45,'G3 D4','Bb3 .21;D4 2.29'),
  (44.11,'A2 E3','C4 .56;E4 2.16')],
 # Wrong side of the rim. An open minor sixth and a late phrase recovery.
 [(0.,'G3 D4','Bb3 .38;A3 1.76'),(5.30,'Eb3 Bb3','G4 1.89;Eb4 3.58'),
  (10.65,'C3 G3','D4 .38;G3 2.54'),(16.07,'F3 C4','A3 .71;C4 2.61'),
  (21.93,'Bb2 F3','F4 .83;C4 2.48'),(27.57,'G3 D4','A3 .53;D4 3.47'),
  (33.48,'Eb3 Bb3','G4 .66;F4 2.88'),(38.81,'D3 A3','A3 .38;E4 2.80'),
  (44.27,'A2 E3','D4 .42;A3 2.22')],
 # Controls. Parts answer each other, but without a constant repeating pulse.
 [(0.,'F3 C4','A3 .48;p:C4 1.95;G4 3.77'),(5.56,'G3 Bb3','D4 .40;p:Bb3 2.06'),
  (10.84,'D3 A3','C4 .79;F4 3.25'),(16.04,'Bb2 F3','A3 .78;p:D4 3.47'),
  (21.34,'E3 Bb3','E4 .47;D4 2.96'),(26.85,'C3 G3','G4 .44;p:E4 3.22'),
  (32.27,'F3 C4','A4 .41;G4 2.21;F4 4.51'),(38.37,'A2 E3','E4 1.42;A3 3.25')],
 # Reprise skips the pulse; four-note motif resolves after 'one bite'.
 [(0.,'D3 A3','D4 .51;A3 2.26;E4 3.77'),(5.37,'Bb2 F3','F4 1.27'),
  (10.72,'G3 D4','D4 .51;Bb3 2.98'),(15.98,'A2 E3','A3 .53;E4 3.05'),
  (21.3,'D3 A3','F4 .49;A4 3.26'),(26.41,'F3 C4','G4 .31;E4 1.97'),
  (30.04,'D3 F3 A3','D4 .61;A3 1.51')],
]


def build_score(bus, meta, play):
    """Write on a score bus using the mixer-provided sample renderer."""
    stages=[f/meta['fps'] for f,_ in meta['chapters']]+[meta['duration_s']]
    track=[]
    for j,movement in enumerate(MOVEMENTS):
        lead=stages[j];end=stages[j+1];power=(.90,.99,.83,.88,.88,.94,1.04)[j]
        for k,(start,chord,figures) in enumerate(movement):
            s=lead+start;nxt=(lead+movement[k+1][0] if k+1<len(movement) else end)
            # Voices overlap by just under a second; every cue follows the written harmony.
            for idx,n in enumerate(chord.split()):
                a=s+idx*.32;d=max(.48,nxt-a+.68)
                play(bus,'cello',n,a,d,-40.3+(.6 if idx==0 else -2.4),(-.26,.32,.10)[idx],power)
                track.append([a,'cello',n,d,j+1]);
            for ph in figures.split(';'):
                n,offset=ph.split();t=s+float(offset)
                voice='pizzicato_strings' if n.startswith('p:') else 'acoustic_grand_piano';n=n.removeprefix('p:')
                d=.94 if voice.startswith('pizz') else 3.77
                db=-42.3 if voice.startswith('pizz') else -38.4+(k%3-1)*.85
                play(bus,voice,n,t,d,db,.24 if voice.startswith('pizz') else -.30+((k%4)*.138),power)
                track.append([t,voice,n,d,j+1])
    return track
