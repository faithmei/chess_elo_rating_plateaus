import requests
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import time

# fetches a player's rating history from Chess.com API
def get_player_stats(username):

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    username = username.lower()

    # chess.com API endpoints
    stats_url = f"https://api.chess.com/pub/player/{username}/stats"
    games_url = f"https://api.chess.com/pub/player/{username}/games/archives"

    try:
        time.sleep(2) # 2-second delay

        # get player's current stats
        stats_response = requests.get(stats_url, headers=headers)
        # prints status code and response for debugging
        print(f"Stats URL Status Code: {stats_response.status_code}")

        if stats_response.status_code != 200:
            print(f"Error accessing stats: {stats_response.status_code}")
            return None, None

        stats_data = stats_response.json()

        time.sleep(2)

        # gets list of monthly game archives
        archives_response = requests.get(games_url, headers=headers)
        print(f"Archives URL Status Code: {archives_response.status_code}")

        if archives_response.status_code != 200:
            print(f"Error accessing archives: {archives_response.status_code}")
            return None, None

        archives_data = archives_response.json()

        return stats_data, archives_data['archives']

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None, None
    except ValueError as e:
        print(f"JSON parsing error: {e}")
        return None, None


def analyze_rating_progression(username, max_archives=3):
    """
    analyzes rating progression over time
    max_archives: maximum number of monthly archives to analyze (most recent ones)
    """
    stats, archives = get_player_stats(username)
    if not stats or not archives:
        return None

    # limits to most recent archives
    archives = archives[-max_archives:] if max_archives else archives
    print(f"Analyzing {len(archives)} monthly archives...")

    # stores rating data
    rating_history = []

    # processes each monthly archive
    for i, archive_url in enumerate(archives):
        try:
            # adds delay between archive requests
            time.sleep(2)  # 2 second delay

            print(f"Fetching archive {i + 1}/{len(archives)}...")
            games_response = requests.get(archive_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })

            if games_response.status_code != 200:
                print(f"Error accessing archive {archive_url}: {games_response.status_code}")
                continue

            monthly_games = games_response.json()['games']
            print(f"Found {len(monthly_games)} games in archive {i + 1}")

            for game in monthly_games:
                date = datetime.fromtimestamp(game['end_time'])

                if game['white']['username'].lower() == username.lower():
                    rating = game['white']['rating']
                else:
                    rating = game['black']['rating']

                rating_history.append({
                    'date': date,
                    'rating': rating,
                    'time_control': game['time_control']
                })


        except KeyboardInterrupt:
            print("\nAnalysis interrupted by user. Processing available data...")

        except Exception as e:
            print(f"Error during analysis: {e}")

    if not rating_history:
        print("No rating history found")
        return None
    print(f"Analyzing {len(rating_history)} games...")


    # converts to DataFrame for analysis
    df = pd.DataFrame(rating_history)

    # calculates rate of rating change
    df = df.sort_values('date')
    df['rating_change'] = df['rating'].diff()
    df['games_played'] = range(len(df))

    # calculates rolling averages
    df['rolling_rating'] = df['rating'].rolling(window=20).mean()
    df['rating_change_rate'] = df['rating_change'].rolling(window=20).mean()

    return df


def plot_rating_progression(df):
    # creates visualization of rating progression

    plt.figure(figsize=(12, 6))

    # plots rating over time
    plt.subplot(2, 1, 1)
    plt.plot(df['games_played'], df['rating'], 'b-', alpha=0.3, label='Actual Rating')
    plt.plot(df['games_played'], df['rolling_rating'], 'r-', label='20-game Moving Average')
    plt.xlabel('Games Played')
    plt.ylabel('Rating')
    plt.title('Rating Progression')
    plt.legend()

    # plots rate of change
    plt.subplot(2, 1, 2)
    plt.plot(df['games_played'], df['rating_change_rate'], 'g-', label='Rate of Rating Change')
    plt.xlabel('Games Played')
    plt.ylabel('Average Rating Change per Game')
    plt.title('Rate of Rating Progress')
    plt.legend()

    plt.tight_layout()
    plt.show()

######################################################
# example:
# username = "YourChessComUsername"
# df = analyze_rating_progression(username)
# plot_rating_progression(df)
# additional analysis functions
######################################################

def find_rating_plateaus(df, window=50, threshold=5):
    # identifies periods where rating progress slows significantly

    df['rolling_change'] = df['rating_change'].rolling(window=window).mean()
    plateaus = []

    current_plateau = None
    for index, row in df.iterrows():
        if abs(row['rolling_change']) < threshold:
            if not current_plateau:
                current_plateau = {
                    'start_rating': row['rating'],
                    'start_game': row['games_played'],
                    'start_date': row['date'] ## added to pinpoint exactly which games the plateaus occur
                }
        elif current_plateau:
            plateaus.append({
                'start_rating': current_plateau['start_rating'],
                'end_rating': row['rating'],
                'games_span': row['games_played'] - current_plateau['start_game'],
                'start_game_number': current_plateau['start_game'], # added to tell the start game number and end
                # game number in which the plateau occurs
                'end_game_number': row['games_played'],
                'start_date': current_plateau['start_date'],
                'end_date': row['date']
            })
            current_plateau = None

    return plateaus


def calculate_progress_metrics(df):
    # calculates various metrics about rating progression

    metrics = {
        'total_games': len(df),
        'initial_rating': df['rating'].iloc[0],
        'final_rating': df['rating'].iloc[-1],
        'total_gain': df['rating'].iloc[-1] - df['rating'].iloc[0],
        'average_gain_per_game': (df['rating'].iloc[-1] - df['rating'].iloc[0]) / len(df),
        'max_rating': df['rating'].max(),
        'min_rating': df['rating'].min(),
        'rating_volatility': df['rating'].std()
    }

    return metrics

def verify_username(username):
    # checks if a Chess.com username exists and is accessible

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    profile_url = f"https://api.chess.com/pub/player/{username}"
    response = requests.get(profile_url, headers=headers)
    print(f"Profile URL: {profile_url}")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Player found: {data.get('username')}")
        return True
    else:
        print(f"Player not found or error occurred. Status: {response.status_code}")
        return False


######################################################
def main():

    # inputs any chess.com username
    username = "MagnusCarlsen"

    max_months = 3

    print(f"Verifying username '{username}'...")
    if verify_username(username):
        print(f"Analyzing data for {username}...")
        df = analyze_rating_progression(username, max_archives=max_months)

        if df is not None:
            # prints overall metrics
            metrics = calculate_progress_metrics(df)
            print("\nOverall Metrics:")
            for key, value in metrics.items():
                print(f"{key}: {value}")

            # finds plateaus
            plateaus = find_rating_plateaus(df, window=30, threshold=3)
            print("\nRating Plateaus:")
            for plateau in plateaus:
                print(f"Plateau at rating {plateau['start_rating']} to {plateau['end_rating']}, "
                      f"lasting {plateau['games_span']} games, "
                      f"from {plateau['start_game_number']} to {plateau['end_game_number']}")

            # creates the visualization
            plot_rating_progression(df)
        else:
            print("Failed to fetch data")
    else:
        print("Please check the username and try again")


# runs script
if __name__ == "__main__":
    main()