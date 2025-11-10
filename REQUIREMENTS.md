The project revolves around personalising the ranking of retrieved documents to each user. You are given some news articles (subset of the original news dataset) along with a user simulation platform. The APIs in the user simulation platform exposes two endpoints, `query` that returns the user query along with the user ID, `ranklist` that takes the ranked list of retrieved documents of that query and returns the list of `actions` for this list. The search platform will have to log the search sessions of `query` and `ranklist` for each user and use this information to improve ranking to the preference of each individual user. There are two sets of features user preference of any given article depends on; topics and one hidden feature. The following will be the steps you will iterate over as part of this exercise.

Your baseline is Elasticsearch that returns the default ranked list without any personalisation.
You will then use the logged data to train and (offline) test different approaches to personalised ranking.
Test statistical gains from such ideas using appropriately designed experiments (consider using AB testing tools like growthbook).

Note that you should target improving the ranking metric as reflected by number of `clicks/dwell-time/like/share/bookmark` actions you observe higher on your ranked list of articles presented to the user with as few calls to the simulation platform as possible.

The user simulation is distributed using a docker image tar.

## Loading and running

**Note:** Loading needs only be done once.

docker load -i ire_project-1.0-amd64.tar
docker run --rm -p 3000:3000 \
 -v $(pwd)/data:/data \
 --tmpfs /tmp:rw,noexec,nosuid \
 --cap-drop ALL \
 --security-opt no-new-privileges \
 ire_project:1.0
The server will start on http://0.0.0.0:3000

`articles.jsonl` contains all the articles that need to be served by your search system. Each line is a JSON object describing one article.

The files can be found in [this link](https://iiithydresearch-my.sharepoint.com/personal/ayan_datta_research_iiit_ac_in/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fayan%5Fdatta%5Fresearch%5Fiiit%5Fac%5Fin%2FDocuments%2FIRE%20Project%20Files&ga=1).

## Endpoints

### GET /query

Samples a random user and query from the loaded data.

**Response:**

```json
{
  "user_id": "8a2f5b18-1a23-4c72-8de1-9c7d4a89ff01",
  "query_id": "7b9f3a12-6d15-4c9f-92da-348ab2a83b10",
  "query_text": "economic recovery 2025"
}
```

**Example:**

curl http://localhost:3000/query

### POST /ranklist

Given a query ID, user ID, and ranked list of article IDs, simulates user actions for each article in the ranked list.

**Request Body:**

```json
{
  "query_id": "7b9f3a12-6d15-4c9f-92da-348ab2a83b10",
  "user_id": "8a2f5b18-1a23-4c72-8de1-9c7d4a89ff01",
  "ranked_article_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440001",
    "550e8400-e29b-41d4-a716-446655440002"
  ]
}
```

**Response:**

```json
{
  "actions": [
    ["Click", { "Dwell": { "secs": 45, "nanos": 123000000 } }, "Like"],
    [],
    ["Click", { "Dwell": { "secs": 20, "nanos": 456000000 } }]
  ]
}
```

**Response Format:**

- actions: Array of action arrays, one for each article in the ranked list
- Empty array [] means the user skipped that article
- Non-empty array contains the sequence of actions:
  - "Click": User clicked on the article
  - {"Dwell": {...}}: Time spent on the article (always follows Click)
  - "Like": User liked the article (optional)
  - "Share": User shared the article (optional)
  - "Bookmark": User bookmarked the article (optional)
