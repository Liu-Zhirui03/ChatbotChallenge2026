# Location-based image knowledge records

All descriptions in this directory are written in English prose. Original image filenames and folder names are retained for traceability. Each `prompt.md` is a factual, image-grounded knowledge document intended for retrieval, rather than an instruction to generate another description. The records follow the supplied workflow: identify the location, describe visible text and spatial information separately, and retain both under the same location. They cover 33 photographs in 19 records, including a nested Wet Lab - Culture Room record and four standalone-image records.

Each subject is described in connected paragraphs. Short headings separate related topics, and source-image links preserve attribution. Visible wording, colors, counts and spatial relationships are included where supported. Counts refer to the visible image rather than an assumed complete inventory. Unreadable text, unknown locations and conflicting notices remain explicit. Document dates do not establish the image capture date, and photographed rules or telephone numbers have not been verified as current.

For Chroma ingestion, split these documents at paragraph or topic boundaries and retain the location name with every resulting chunk. If a paragraph is too long for the configured embedding model, split it at sentence boundaries. Carry the source links, record path, section title and chunk position as metadata; also retain `kind=image_description`, `content_type=image/jpeg`, the review date `2026-10-13`, and an unknown capture date. The original image path is the stable local source identifier. Preserve multiple source links when a section combines images. Unknown-location records must remain unknown rather than acquiring a room name from a nearby record. Avoid indexing this README as factual evidence about the building.

Embedding these records and adding them to Chroma makes them retrievable knowledge; it does not train or fine-tune the chatbot model. These files have not yet been embedded or imported into Chroma. Keep the raw images separate so descriptions and the database can be rebuilt. Future additions to this directory should continue using English paragraphs with the same source attribution and evidence boundaries.

## Records

[Brainstorm Space / Brainstorming Area](Brainstorm_Space/prompt.md)

[Digital Learning Studio](Digital_Learning_Studio/prompt.md)

[Dream Chamber](Dream_Chamber/prompt.md)

[Multi-Purpose Room](Multi-Purpose_Room/prompt.md)

[Podcast Studio](Podcast_Studio/prompt.md)

[Project Studio A](Project_Studio_A/prompt.md)

[Project Studio B](Project_Studio_B/prompt.md)

[Thematic Workshop D](Thematic_Workshop_D/prompt.md)

[Thematic Workshop E](Thematic_Workshop_E/prompt.md)

[Wet Lab - Culture Room](Thematic_Workshop_G/Wet_Lab_Culture_Room/prompt.md)

[Machine Workshop](Machine_Workshop/prompt.md)

[Open Event Area](Open_Event_Area/prompt.md)

[Thematic Workshop F](Thematic_Workshop_F/prompt.md)

[Thematic Workshop G](Thematic_Workshop_G/prompt.md)

[Thematic Workshop H](Thematic_Workshop_H/prompt.md)

[Innovation Wing student research assistant entry notice](微信图片_20261013104634_77_35/prompt.md)

[Tam Wing Fan Innovation Fund funding poster](微信图片_20261013104642_85_35/prompt.md)

[LG directional sign](微信图片_20261013104643_86_35/prompt.md)

[Electronics workbench at an unidentified location](微信图片_20261013104644_87_35/prompt.md)
