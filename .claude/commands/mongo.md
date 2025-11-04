# Mongo Agent 

Query the MongoDB to answer the `request` frome the user. 

## Instructions

### Relevant Files 
-You can find the .env in the parent folder of `dumplin_production`. Just look one folder above. 
-We have included samples of the collections in `dumplin_production/mongo_db_samples`
-We have also included `dumplin_production/mongo_db_samples/collections.md` to explain the relationships between data. 

### Operating Procedure
- Any files that you create to answer the question need to be created on the `dumplin_production/TMP` folder.


### Report 
- Give a concise 2-3 sentence summary in outline format of what you have accomplished, giving the highlight and answering the question. 

## Important 
- In the place_embeddings collection, the city is already the city from City_boundaries (this collection only has places within the city boundaries). But on the places collection, this is the raw city from google maps
- Be concious of UnicodeEncodeErrors.