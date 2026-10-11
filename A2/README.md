# Group 35

## A2a

### Member 1: 2

### Member 2: 2

### Member 3: 2

## A2b

**Q: Select which building(s) to focus on for your focus area**

The team chose teh reports for building: 2602, 2603 & 2608:<br>

Building 2602:<br>
*“The project will also highlight areas of opportunities where sustainability performance has potential to be improved, while keeping potential considerations of regulatory requirements and environmental trade- offs in mind. Economic sustainability will be evaluated through a life cycle costing (LCC) analysis”* (Section 6, page 29)<br>

Building 2603:<br>
*“The Life Cycle Inventory for the proposed material palette provides a structured basis for evaluating the environmental and practical implications of the renovation and extension. In this assessment, each material is characterized not only by its embodied climate impact, but also by waste generation during implementation, and the anticipated end-of-life route. In addition, the inventory is complemented by key economic and operational indicators such as material cost, installation and maintenance cost, operational energy implications, and waste management costs - to ensure that the selected solutions are robust over the full building life cycle.”* (Section 3.3, page 10)<br>

Building 2608:<br>
*“For the new materials in the renovation project the materials consultants have will make a material catalog highlighting the GWP-impact of each of the options. This will be presented for the other roles and the goal is to pick the new materials with the lowest GWP-output while still satisfying each of the other roles.”* (Section 5.3, page 38)<br>

**Q: Identify a ‘claim’ / issue / fact to check from one of those reports.**<br>
Report 2608 claims that new materials can be selected by the lowest GWP by LCA assessments combined with other factors such as financial and energy implications.<br>
This facilitates a more centralized and properly process of selecting materials. 

**Q: Write a short description of the claim you wish to check.**<br>
We want to check whether the lowest-GWP material choice for an element actually remains the best choice once thermal performance (U-value) and life cycle cost are considered. To do this, we extract the material layers, GWP and U-value of the exterior walls (and other elements, if available) from the Blender/IFC model and compare the alternatives on all parameters at once.

**Q: Justify your selection of your claim**<br>
Selecting materials on GWP alone is simple, but it can have deceiving trade-offs: a low-GWP wall may have a poor U-value, which increases operational energy use, or a higher maintenance and replacement cost over time. The claim also seems 'checkable'. It of course depends on the data available can be extracted from the IFC model (layers, thickness, U-value, e.g.) and linked to EPD data. Finally, the claim matters most in renovation, where the choice between replacing and renovating an element has large consequences.


## A2c
**Q: How you would check this claim?**<br>
Firstly, it would be wise to test whether the relevant data about the walls, slabs etc. are avaliable in the IFC model. Afterwards, we reuse a previous group's tool that already assesses building materials and properties, adding the attributes we need (U-value, cost, lifetime). Third, we link each material layer to EPD data to calculate GWP and compare the result across different wall typologies.

**Q: When would this claim need to be checked?**<br>
Information about materials are usually most valuable in the design phases of the building. In the case of a renovation, this information would be most valuable during the assesment of the building construction, in regards to how much CO2 it would take to replace an element entirely or renovate it. It is also good practice to follow the GWP of materials throughout the project as the design changes.

**Q: What information does this claim rely on?**<br>
The claims in the reports and the data available in the model (IFC elements, material layers, property sets), together with EPD and cost data.

**Q: What phase? planning, design, build or operation.**<br>
Planning and design phases are the most important phases in terms of choosing materials. These stages has the biggest flexibility in regards to the material choices. Because of this, these stages can also be be overwelming for the consultatns, as they need to make a lot of decisions in due time. This can lead to decisions made based of off 'BAU' (Buisness as usual) decisions, that might not be reflect the actual needs of the occupants or the building owner. 

**Q: What BIM purpose is required? Gather, generate, analyse, communicate or realise?**<br>
Primarily analyse: the tool hopes to evaluate building elements across different parameters (GWP, U-value, cost). It also supports communicate, as the results are presented to the consultant as a basis for decision making.

**Q: Review use case examples - do any of these help?, What BIM use case is this closest to?**<br>
A report there is close to this studys case could be 2438. 2438 aims to match relevant IFC data with EPD data automatically. Their script extracts the IFC layers and match them with the relevant EPD data to sum the total GWP of the building materials. 

**Q: Produce a BPMN-diagram for your chosen use case. Link to this so we can see it in your markdown file. To do this you will have to save it as an SVG, please also save the BPMN with it. You can use this online tool to create BPMN-diagrams.**<br>
![Alt text](https://github.com/Andreaszk04/MAT_26_35/blob/main/A2/diagram%20(5).svg)

## A2d

**Q: From the ‘whole use case’ identify where a new script / function / tool is needed. Highlight this in your BPMN diagram. Show this clearly in a new SVG diagram.**<br>


## A2e

**Q: Describe in words your idea for your own OpenBIM ifcOpenShell Tool in Python.**<br>
The idea is to make a tool that is able to assess the consequenses of the downstream material choices for an exterior wall over a 50 year period. The tool will asses the wall's material layers and dimensions from the IFC model, links them to EPD data, and calculates GWP over 50 years and life cycle cost for each alternative. The tool will then compare different wall typologies and compare them on the bases of predetermined performance variables such as loads, insulation (heat transfer), maintenance and temperature change due to climate change are used to compare the alternatives.

This tool will be utilized best in the early design stages. The tool aims to provide the consultants to make informed decisions. 

**Q: What is the business and societal value of your tool?**<br>
Business perspectiv: The consultant gets a fast overview of the long-term consequences of material choices, so decisions are based on data instead of business as usual. This reduces the risk of changes later in the project and supports documentation for sustainability requirements.

Societal perspectiv: Lower embodied and operational emissions across the life cycle, fewer poor material choices that must be corrected later, and buildings that perform well for their users over the long term.

**Q: Produce a BPMN diagram to summarize your idea. Save this in a folder in your repository along with an SVG of the diagram and embed the SVG in the Markdown as an image.**<br>
![Alt text](https://github.com/Andreaszk04/MAT_26_35/blob/main/diagram%20(4).svg) 

## A2f

**Q: Identify what information you need to extract from the model.**<br>
To make our tool function, we need to extract information about the exterior walls. For an exterior load-bearing wall: the material layers and their thicknesses, the orientation of the wall, its dimensions (length, height, area), the U-value, and GWP if available. Openings (windows) are needed to calculate the net wall area.

**Q: Where is this in IFC?**<br>
- IFCWall
- IFCMaterial
- IFCWindow
- IFCElementQuantity
<br>

**Q: Is it in the model?**<br>
To our knowledge, this data is mostly available in the IFC. GWP is rarely stored in IFC models, so we expect to link GWP from external EPD data. 

**Q: Do you know how to get it in ifcOpenShell?**<br>
Partly. We expect to use ifcopenshell.open(), model.by_type("IfcWall"), and ifcopenshell.util.element.get_material() and get_psets().

**Q: What will you need to learn to do this?**<br>
We need to learn how to extract relevant data using IfcOpenShell. We also need to lear how to how to match material names to EPD entries, and how to structure the calculation for GWP and LCC over 50 years.

## A2g

**Q: What software license will you choose for your project?**<br>
Visual Studio Code(?)<br>
License for Blender(?)
