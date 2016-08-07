import matplotlib.pyplot as plt
import sqlite3
import sys
state_abbreviation = sys.argv[1]


query = '''SELECT
    r.state, r.county, 
    (SELECT SUM(r2.votes) FROM primary_results r2 where r2.state = r.state AND r2.county = r.county AND r2.candidate = 'Hillary Clinton') as clinton_votes,
    (SELECT SUM(r2.votes) FROM primary_results r2 where r2.state = r.state AND r2.county = r.county AND r2.candidate = 'Bernie Sanders') as sanders_votes,
    SUM(r.votes) as total_votes, c.PST045214 as population
FROM primary_results r
LEFT JOIN county_facts c ON c.state_abbreviation = r.state_abbreviation AND c.area_name = r.county || ' County'
WHERE r.state_abbreviation = '{}' AND r.party = 'Democrat'
GROUP BY r.state, r.county, c.PST045214
HAVING total_votes > 0
ORDER BY total_votes;'''

query = query.format(state_abbreviation)

xs, y_clinton, y_sanders = [], [], []

cumulative_clinton_voters = 0
cumulative_sanders_voters = 0
cumulative_voters = 0

con = sqlite3.connect('database.sqlite')
cur = con.cursor()
vote_data = cur.execute(query)

for row in vote_data.fetchall():
    state,county,clinton_votes,sanders_votes,total_votes,population = row
    cumulative_voters += int(total_votes)
    cumulative_clinton_voters += int(clinton_votes)
    cumulative_sanders_voters += int(sanders_votes)
    xs.append(cumulative_voters)
    y_clinton.append(float(cumulative_clinton_voters) / cumulative_voters - 0.5)
    y_sanders.append(float(cumulative_sanders_voters) / cumulative_voters - 0.5)

if not xs:
    raise Exception("no data found for state {}".format(state_abbreviation))

# turn x-axis into percentage
xs = [100. * x / cumulative_voters for x in xs]

abs_lim = max(max(map(abs, y_clinton)), max(map(abs, y_sanders)), 0.2)

# plot
for log_scale in (False,):
    plt.figure()
    plt.scatter(xs, y_clinton, label='clinton', color='blue')
    plt.scatter(xs, y_sanders, label='sanders', color='red')
    if log_scale:
        plt.gca().set_xscale('log')
    plt.xlim(0, 100)
    plt.xlabel('cumulative vote total')
    plt.ylim(-abs_lim, abs_lim)
    plt.ylabel('deviation from mean')
    plt.title(state_abbreviation)
    plt.legend()

plt.savefig('{}.png'.format(state_abbreviation))
