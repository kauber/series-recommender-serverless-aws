import json
import boto3
import logging

# Initialize AWS S3 client and logger
s3 = boto3.client('s3')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        # Log the incoming event
        logger.info(f"Received event: {event}")

        # Input parameters
        params = event.get('queryStringParameters', {})
        genre = params.get('genre', '').lower()
        from_year = int(params.get('fromYear', 0))
        to_year = int(params.get('toYear', 9999))
        country = params.get('country', 'Other')
        seasons = params.get('seasons', 'more')

        

        # Validate genre parameter
        if not genre:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Genre parameter is required."})
            }

        # Construct the file name based on the genre
        file_key = f"{genre}_data.json"
        bucket_name = 'tv-series-recommender-data-767397959554-eu-central-1'

        # Fetch the genre-specific file from S3
        logger.info(f"Fetching file: {file_key}")
        response = s3.get_object(Bucket=bucket_name, Key=file_key)
        data = json.loads(response['Body'].read().decode('utf-8'))
        logger.info(f"Loaded {len(data)} records from S3.")

        # Filter and sort data
        filtered_data = []
        for series in data:
            # Check year range
            release_year = series.get('release_year', 'Unknown')
            if release_year != "Unknown" and (int(release_year) < from_year or int(release_year) > to_year):
                continue

            # Check country
            countries = series.get('country', ['Unknown'])
            if country != 'Other' and country not in countries:
                continue
            if country == 'Other' and any(c in countries for c in ['US', 'CN', 'GB', 'JP', 'DE', 'KR', 'CA', 'FR']):
                continue

            # Check number of seasons
            num_seasons = series.get('number_of_seasons', 0)
            if seasons == '1' and num_seasons != 1:
                continue
            if seasons == '2' and num_seasons != 2:
                continue
            if seasons == 'more' and num_seasons <= 2:
                continue

            # Add series to filtered list
            filtered_data.append(series)

        # Sort by popularity
        filtered_data = sorted(filtered_data, key=lambda x: x.get('popularity', 0), reverse=True)

        # Get the top 5 results
        top_results = filtered_data[:5]

        # Format the response
        results = []
        for series in top_results:
            results.append({
                'Title': series.get('title', 'Unknown'),
                'Year': series.get('release_year', 'Unknown'),
                'Country': ", ".join(series.get('country', ['Unknown'])),
                'Description': series.get('description', 'No description available'),
                'Vote Average': series.get('rating', 'Unknown'),
                'Poster Path': f"https://image.tmdb.org/t/p/w500{series.get('poster_path')}" if series.get('poster_path') else None
            })

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"results": results})
        }

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }
