"""Picture lock is NOT implied: this is the first animatic over the v2 WAV.

Times are on the measured v2 timeline (seconds), before rounding to 24 fps.
Regional map points are not exact specimen positions. Illustration text is
intentional and should survive a later picture upgrade.
"""
from dataclasses import dataclass

FPS = 24
END = 445.667


@dataclass(frozen=True)
class Shot:
    at: float
    style: str
    variant: str
    heading: str
    deck: str
    tag: str
    edit: str


S = Shot
SHOTS = (
    S(0, 'map', 'open', 'Two sets\nof tracks', 'Brazil and Cameroon', 'PRESENT DAY', 'On the first word, show schematic track and Sousa. Light Koum on “More in Cameroon” (2.645). Add the distance scale at 6.225; no route line.'),
    S(10.225, 'map', 'rewind', 'Take away\nthe ocean', 'Model snapshot • not a footprint date', 'RECONSTRUCTION', 'Hard match-cut at “But rewind the map,” at the same geographic scale. Study estimate appears at 15.395.'),
    S(19.585, 'title', '', 'Why These Dinosaur\nFootprints Are\nan Ocean Apart', '', 'EXTINCT LIFE', 'Title after the reveal, over ancient cartography. No ident before the hook.'),
    S(26.195, 'map', 'focus', 'Start with\nthe rock', 'Koum Basin, northern Cameroon', 'REGIONAL LOCATION', 'Cut back to modern location. Hold the regional Koum pin without moving a dinosaur across the water.'),
    S(32.63, 'stack', 'preview', 'Four ancient\nsurfaces', 'Four different pieces of ground', 'FIELD OBSERVATION', 'Tease the layers before the scene window changes.'),
    S(36.192, 'photo', 'mayo', 'The Mayo Rey\nRiver', 'Koum Basin  /  Cameroon', 'LANDSCAPE ILLUSTRATION', 'Generalized riverbed artwork, not field footage or an exact rendering of KB-17.'),
    S(43.338, 'imprint', 'count', 'Counting the\nimpressions', 'Koum Basin survey · one site', 'FIELD OBSERVATION', 'Reveal the 283 footprint count at 45.538. Do not equate prints with animals.'),
    S(48.078, 'tracks', 'way', 'One animal.\nSeveral steps.', 'A sequence of steps is a trackway.', 'HOW TO READ A TRACK', 'Progressively light the illustrative steps on one small slab. Add 34 documented trackways at 52.778.'),
    S(55.488, 'tracks', 'stop', 'The record\nstops here', 'Steps can show movement on this patch.', 'TRACKWAY SCHEMATIC', 'Read direction within the slab. End abruptly at the edge; no footprints beyond it.'),
    S(64.558, 'stack', 'four', 'Not one\nsurface', 'Separate bearing layers, not one herd', 'FIELD OBSERVATION', 'Explode four bedding surfaces on “not all on the same surface.” No equal-time interpretation.'),
    S(75.198, 'stack', 'erosion', 'The site\nis changing', 'Erosion can remove parts of the record.', 'FIELD OBSERVATION', 'Illustrative spalling edge, not a comparison of actual surveys.'),
    S(84.158, 'scan', 'views', 'Photographs\nthat overlap', 'How photogrammetry works', 'METHOD SCHEMATIC', 'Illustrate several views of the same slab. Add “2,000+ images” at 87.838; not all of a single specimen.'),
    S(90.518, 'scan', 'relief', 'A surface\nin 3D', 'Selected slabs were modelled.', 'METHOD SCHEMATIC', 'The mesh resolves to shaded relief; it is procedural, not the field team’s mesh.'),
    S(95.898, 'imprint', 'tease', 'One very\nlarge print', 'A three-toed impression at Koum', 'TRACK SCHEMATIC', 'Hold off on the ruler until the next section.'),
    S(101.763, 'imprint', 'ruler', '≈69 cm', 'Length of the impression, not animal height', 'MEASURED IMPRESSION', 'Bring in ruler on the number (102.107). TK-034 mean hind-print length; outline is not the measured specimen.'),
    S(110.337, 'imprint', 'diffuse', 'A blurred\noutline', 'Softer sediment may have deformed.', 'PRESERVATION INTERPRETATION', 'Raking light makes fuzzy margins legible without claiming to recreate the specimen.'),
    S(120.707, 'stamp', 'press', 'Same foot.\nDifferent mud.', '', 'SUBSTRATE DEMONSTRATION', 'One repeatable three-toed stamp at the same scale. Compare firm edge retention and soft wall slump.'),
    S(131.897, 'stamp', 'results', 'Two different\nmarks', 'Both came from the same stamp.', 'SUBSTRATE DEMONSTRATION', 'Top-down crisp versus diffuse result, held for comparison.'),
    S(136.357, 'tracks', 'changes', 'Even on\none trackway', 'The same steps can read differently.', 'TRACKWAY SCHEMATIC', 'Fade clarity left to right along one schematic sequence; J24 describes this variability.'),
    S(143.917, 'stamp', 'other', 'One shape,\nmany makers', 'Three toes are not a species ID.', 'LIMIT OF THE EVIDENCE', 'Two generic outlines on separate panels. No claim about who made either site’s tracks.'),
    S(150.307, 'bed', 'sections', 'What was under\ntheir feet?', 'Compare the ground, not just the outline.', 'PRESERVATION COMPARISON', 'Match-cut from plan-view relief to a sediment section.'),
    S(155.883, 'textures', 'marks', 'Read the\nsurface', 'Look past the toes.', 'ROCK TEXTURE SCHEMATICS', 'Show ripple evidence at 157.688 and exposed dry surface at 160.828. Schematic textures, not micrographs.'),
    S(163.418, 'bed', 'clues', 'The ground\nchanged', 'Ripples and cracks can survive in different beds.', 'SEDIMENT SCHEMATIC', 'Flag separate beds with separate clues, not a single simultaneous event.'),
    S(168.648, 'bed', 'drain', 'Water off.\nGround exposed.', 'A shallow margin can change state.', 'ILLUSTRATIVE SEQUENCE', 'A slice through a gentle lake margin; water level drops and an impression becomes possible.'),
    S(175.698, 'imprint', 'fade', 'A print can\nvanish', 'Why did these last?', 'PRESERVATION QUESTION', 'Dissolve an illustrative shallow imprint, leaving the question open.'),
    S(182.758, 'micro', 'cement', 'Between\nthe grains', 'Mineral cement joins fine grains.', 'THIN-SECTION SCHEMATIC', 'Do not use the journal micrograph. Reveal bridges between grains, not a claim about exact hardening time.'),
    S(194.468, 'micro', 'mat', 'A thin\nbinding layer', 'Possible microbial mat', 'PRESERVATION INTERPRETATION', 'Show a thin mat at the surface; no depiction of recovered living microbes.'),
    S(202.968, 'bed', 'bury', 'Buried before\nit washed out', 'Fresh sediment can seal the impression.', 'ILLUSTRATIVE SEQUENCE', 'Cover the depressed surface while leaving the outline of the buried bed distinct.'),
    S(208.058, 'imprint', 'preserved', 'From step\nto trace', 'The ground helped preserve the mark.', 'PRESERVATION SCHEMATIC', 'Return to a fixed geological imprint, not an animated dinosaur.'),
    S(214.083, 'map', 'sousa', 'Across the\nAtlantic today', 'Sousa Basin, northeastern Brazil', 'PRESENT DAY', 'Point to Sousa; transition the viewer, not an animal, across the modern gap.'),
    S(218.918, 'photo', 'sousa', 'The Sousa\nBasin', 'Shallow-lake and river deposits', 'LANDSCAPE ILLUSTRATION', 'Generalized riverbank artwork, not a locality photograph.'),
    S(223.008, 'micro', 'sousa', 'Clues in\nthe texture', 'Textures attributed to microbial mats', 'PRESERVATION INTERPRETATION', 'Brazilian study presented as a separate line of evidence.'),
    S(228.958, 'imprint', 'rim', 'The pushed-up\nrim', 'Sediment displaced around the print', 'SOUSA SCHEMATIC', 'Time the rim callout to “raised rims” at 230.718. Original outline, not a fossil photograph.'),
    S(234.878, 'bed', 'rim', 'A rim\nthat held', 'More cohesive ground could hold the edge.', 'PRESERVATION INTERPRETATION', 'Cross-section of the raised edge on one generalized impression.'),
    S(240.968, 'compare', 'ground', 'The resemblance\nis in the ground', 'Different basins. Similar preservation conditions.', 'COMPARING THE DEPOSITS', 'Use distinct substrate textures and separate locality labels; no specimen matching.'),
    S(251.138, 'compare', 'banks', 'Similar is not\nthe same as linked', 'Two riverbanks can look alike.', 'LIMIT OF THE EVIDENCE', 'Two separate landscape vignettes rather than matched silhouettes.'),
    S(262.068, 'age', 'unmatched', 'Side by side\non the screen', 'Not necessarily side by side in time', 'AGE LIMIT', 'Use intentionally uncorrelated beds, no dated gap assigned to either print.'),
    S(270.685, 'age', 'window', 'A window\nof time', 'Not a timestamp for a step', 'REGIONAL AGE EVIDENCE', 'Keep ages broad and uncertainty obvious.'),
    S(274.193, 'micro', 'pollen', 'Fossil\npollen', 'One clue to the age of nearby deposits', 'POLLEN SCHEMATIC', 'Generic diagram; no particular taxon claimed to date the tracked bed.'),
    S(280.383, 'age', 'regional', 'From other\nlayers', 'Regional clues do not date each footprint.', 'REGIONAL AGE EVIDENCE', 'Place sample markers in surrounding strata, not on the print surfaces.'),
    S(287.463, 'age', 'broad', 'Early\nCretaceous', 'Too broad to show they walked at the same time', 'AGE LIMIT', 'No numerical ages or shared exact date stamp.'),
    S(294.673, 'map', 'restore', 'Restore the\ngeography', 'Not a puzzle made from footprint outlines', 'RECONSTRUCTION', 'Return to the 125 Ma model, keep “not a footprint date.”'),
    S(301.243, 'fault', 'structures', 'Look below\nthe coastline', 'Older rocks and faults inform the reconstruction.', 'STRUCTURE SCHEMATIC', 'A generic faulted block; no unmapped fault line on the regional map.'),
    S(305.903, 'map', 'structural', 'Before\nseparation', 'Geological structures tie the regions together.', 'RECONSTRUCTION', '2024 reconstruction discussed in VO. Visual map is the independently licensed 125 Ma context, not J24 artwork.'),
    S(312.463, 'fault', 'sink', 'As the crust\nstretched', 'A fault-bounded low area forms.', 'RIFTING SCHEMATIC', 'Animate stretching downward into the basin, not a dinosaur-time jump.'),
    S(320.433, 'fault', 'fill', 'Separate pieces\nof the record', 'Rivers and lakes left sand and mud.', 'BASIN SCHEMATIC', 'Show accumulated fill; no exact track site geometry.'),
    S(327.976, 'map', 'joined', 'Land\nin between', 'Connected land is only the first clue.', 'RECONSTRUCTION', 'At the act turn, no travel arrow on connected land.'),
    S(332.659, 'photo', 'valley', 'Where could\nlife move?', 'Rivers and lakes, not a bare map', 'LANDSCAPE ILLUSTRATION', 'Hypothetical landscape, not a view reconstructed for either set of tracks.'),
    S(342.989, 'map', 'possible', 'Could valleys\nconnect them?', 'Possible dispersal area • not a traced route', 'DISPERSAL HYPOTHESIS', 'At 345.829 put an unbounded diffuse highlight on connected land. Never outline a measured corridor.'),
    S(348.789, 'network', 'generations', 'Over many\ngenerations', 'A possible habitat connection', 'DISPERSAL HYPOTHESIS', 'Separate habitat pools fill; no one animal or directional march across a map. Conceptual, not geography.'),
    S(357.009, 'fish', 'intro', 'A clue without\nfootprints', 'Fish fossils from other basins', 'SEPARATE FOSSIL EVIDENCE', 'Reveal the coelacanth illustration during the line naming it. Not a fossil at either track site.'),
    S(366.709, 'fish', 'basins', 'A separate\npattern', 'The finds do not trace a single river.', 'SEPARATE FOSSIL EVIDENCE', 'Show basin-group labels without pins at the footprint sites. No claim of the same fish species.'),
    S(376.789, 'network', 'test', 'A pattern\nto test', 'Compare separate finds with the geography.', 'DISPERSAL HYPOTHESIS', 'Two independent clues plus a model, not a proven trail.'),
    S(381.969, 'network', 'better', 'What would\nhelp?', 'Evidence to look for, not newly found fossils', 'OPEN QUESTION', 'Accumulate: intervening sites, narrower dates, more identifiable fossils.'),
    S(395.029, 'map', 'possible-end', 'A possible\nroute', 'Not a journey recorded in stone', 'DISPERSAL HYPOTHESIS', 'Hold a soft area, then remove it for the separation payoff.'),
    S(402.879, 'fault', 'stages', 'The ocean\nopened in stages', 'Land connection → widening ocean', 'PLATE MOTION SCHEMATIC', 'Stylized staged separation, not a dated coast interpolation or a single abrupt split.'),
    S(412.379, 'map', 'back', 'The gap\nis back', 'Approximate modern separation', 'PRESENT DAY', 'Cut back to the opening geography on “the ocean widened.” Hold before the last reveal.'),
    S(418.979, 'map', 'question', 'What really\nmade the journey?', '', 'PRESENT DAY', 'Leave the two pins in place while the question lands.'),
    S(423.739, 'map', 'rocks', 'The rocks.', 'The footprints stayed in their beds.', 'PRESENT DAY', 'Answer on the spoken line, without animating a dinosaur crossing.'),
    S(429.819, 'imprint', 'end', 'One step.\nA lost landscape.', '', 'TRACK SCHEMATIC', 'Quiet last image. The story is where life could go, not a witnessed journey.'),
    S(439.167, 'credits', '', 'Sources & maps', '', 'EXTINCT LIFE', '6.5 s tail after the full v2 WAV. No score; visible map license and source credit.'),
)


def frames():
    return [round(s.at * FPS) for s in SHOTS] + [round(END * FPS)]
