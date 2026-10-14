# SIH Comprehensive Judge Q&A Database

This document simulates a rigorous Q&A session with university professors judging your project. The questions progress from basic understanding to deep algorithmic scrutiny. All answers are strictly mapped to the `STUDY_GUIDE.md` facts.

## Section 1: The Basics (Quick Answers)

**Q1. Professor:** "Can you explain what your software actually does in simple terms?"
**Answer:** "Our software, DepthWizard, takes a standard flat 2D satellite image and uses AI to instantly predict the 3D elevation of that terrain, rendering it into an interactive 3D map in under 5 seconds."

**Q2. Professor:** "Why didn't you just use traditional LiDAR or Radar like everyone else does for 3D mapping?"
**Answer:** "Traditional methods like LiDAR flights or multi-view stereopsis take hours or even days of computation on massive GPU clusters, and they are incredibly expensive. In a sudden disaster like a flood, responders need 3D data instantly. Our software provides that in 5 seconds from cheap optical imagery."

**Q3. Professor:** "You mentioned the AI is 'Zero-Shot'. What does that actually mean?"
**Answer:** "'Zero-shot' means the AI can predict depth on entirely new images it has never seen before in its training data. We didn't have to spend months training a custom model on a narrow satellite dataset; we used a generalized foundational model."

## Section 2: AI Mechanics & The Domain Gap (Medium Explanations)

**Q4. Professor:** "What is the 'Domain Gap' you listed on your risks slide, and why did it happen?"
**Answer:** "Most AI models are trained on forward-facing photos (like looking down a street). When you feed them a 'nadir' (straight top-down) satellite image, they get confused. This 'domain gap' causes them to smoothly blur the sharp edges of building rooftops into the ground."

**Q5. Professor:** "How did you solve this domain gap blurring for city buildings?"
**Answer:** "We integrated a secondary AI called FastSAM (Fast Segment Anything). It actively hunts for building footprints in the image, cuts them out, and mathematically flattens the predicted depth inside that mask to keep roofs perfectly sharp."

**Q6. Professor:** "I see you boast a 5-second latency. Doesn't running a secondary segmentation AI slow everything down?"
**Answer:** "No, because we specifically chose *FastSAM*, which runs at 50x the speed of the original SAM model. It processes masks in under 40 milliseconds, allowing us to flatten buildings without bottlenecking the main 5-second pipeline."

**Q7. Professor:** "What happens if I put an image of a natural canyon through that building-flattening pipeline?"
**Answer:** "It creates what we call the 'Minecraft Canyon' effect. The algorithm tries to find structures in the rocks and flattens the slopes into jagged, stair-stepped blocks. We solved this by building a 'Context-Aware' toggle that completely bypasses the segmentation step for natural terrain."

## Section 3: Geospatial Math & Scale (Deep Explanations)

**Q8. Professor:** "If your AI only predicts relative depth values between 0.0 and 1.0, how are you outputting actual measurements in meters?"
**Answer:** "We perform metric calibration using open-source global data. Our backend reads the coordinates of the uploaded image and pulls a low-resolution SRTM (Shuttle Radar Topography Mission) 30-meter elevation anchor from NASA to use as a baseline."

**Q9. Professor:** "How exactly do you map your high-res 0-1 AI output against that low-res SRTM anchor? Are you just multiplying them?"
**Answer:** "No, standard linear scaling fails because water reflections or AI errors create massive outliers. We use RANSAC (Random Sample Consensus) statistical regression. It mathematically stretches our relative AI predictions into exact real-world meters while actively ignoring and rejecting those chaotic outliers."

**Q10. Professor:** "Did RANSAC actually make a difference compared to standard scaling?"
**Answer:** "Yes, our empirical testing showed that RANSAC improved absolute elevation accuracy by roughly 41% by aggressively rejecting those localized terrain outliers."

## Section 4: Validation & Accuracy (Detailed Defenses)

**Q11. Professor:** "How do you prove to us that your AI-generated 3D map is actually accurate and not just a hallucination?"
**Answer:** "We built an automated validation engine. The user can upload Ground Truth (GT) LiDAR data, and our system will directly compare our generated DSM against the true LiDAR to calculate precise Root Mean Square Error (RMSE) metrics."

**Q12. Professor:** "But satellite images and LiDAR scans usually have different grid resolutions and coordinate systems. How can you compare them directly without crashing the system?"
**Answer:** "That was a major engineering hurdle. We utilized the `rasterio` Python library on our backend to automatically reproject and spatially resample (using Bilinear interpolation) the Ground Truth LiDAR so that its grid perfectly aligns with our generated DSM before running the math."

**Q13. Professor:** "Besides raw numbers, how is a user supposed to know where the AI failed in a disaster scenario?"
**Answer:** "Our validation engine doesn't just output an RMSE number. It dynamically generates a spatial `ERROR HEATMAP`. It overlays red and blue color zones directly onto the 3D WebGL viewer so users can visually pinpoint exactly where the topography predictions failed."

## Section 5: Software Architecture & Feasibility (System Defenses)

**Q14. Professor:** "Foundational models like Depth Anything V2 are massive. How are you expecting disaster responders to run this without an expensive cloud GPU cluster?"
**Answer:** "We engineered our FastAPI backend for 'VRAM Hot-Swapping'. The massive AI models are not kept running constantly. They are dynamically loaded into VRAM only during the 3-second active inference window and then instantly purged, allowing the system to run on consumer-grade hardware."

**Q15. Professor:** "When your system exports these massive high-res GeoTIFFs to the web browser, doesn't it cause the browser to crash from memory overload?"
**Answer:** "It did initially. Generating 20MB+ Float32 binaries in JavaScript causes severe memory leaks. We engineered an explicit Garbage Collection system using `URL.revokeObjectURL()` that violently flushes the binary Blob from the user's RAM exactly 5 seconds after they click download."
