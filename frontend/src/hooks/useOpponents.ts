import { useState, useMemo } from 'react';
import {
  Opponent,
  OpponentFilter,
  OpponentSort,
} from '@/types/opponent';

const mockOpponents: Opponent[] = [
  {
    id: 'opp-1',
    gamertag: 'xXDragonSlayerXx',
    archetype: 'Aggressive Rusher',
    encounterCount: 8,
    lastSeen: '2d ago',
    winRate: 62,
    isRival: true,
    record: { wins: 5, losses: 3 },
    blitzFrequency: 72,
    scoutedAt: '2026-02-15',
    formationFrequencies: [
      { formation: 'Nickel 3-3-5', percentage: 35 },
      { formation: 'Dollar', percentage: 25 },
      { formation: '4-3 Over', percentage: 20 },
      { formation: 'Big Dime', percentage: 12 },
      { formation: '3-4 Bear', percentage: 8 },
    ],
    archetypeDetail: {
      description: 'Heavy blitz pressure with aggressive man coverage. Relies on speed rush and interior stunts to collapse the pocket quickly.',
      strengths: ['Relentless pass rush', 'Forces quick decisions', 'Strong run-stuff on early downs'],
      weaknesses: ['Vulnerable to screens', 'Weak against misdirection', 'Gives up deep shots when blitz fails'],
    },
    tendencies: [
      { label: 'Man Coverage', percentage: 68, category: 'defense' },
      { label: 'Zone Blitz', percentage: 45, category: 'defense' },
      { label: 'Run Stuff', percentage: 55, category: 'defense' },
      { label: 'Speed Rush', percentage: 72, category: 'offense' },
      { label: 'Play Action', percentage: 30, category: 'offense' },
      { label: 'RPO', percentage: 22, category: 'offense' },
    ],
    playFrequencies: [
      { playName: 'Cover 0 Blitz', count: 24, successRate: 58 },
      { playName: 'Pinch Buck O', count: 18, successRate: 52 },
      { playName: 'Tampa 2', count: 12, successRate: 45 },
      { playName: 'Mid Blitz', count: 15, successRate: 62 },
      { playName: 'DB Fire 2', count: 10, successRate: 48 },
    ],
    weaknesses: [
      { area: 'Screen Defense', severity: 'critical', description: 'Consistently over-pursues, leaving screen lanes open', exploitPlay: 'HB Screen' },
      { area: 'Deep Coverage', severity: 'high', description: 'Single-high safety leaves deep sideline exposed when blitzing', exploitPlay: 'Four Verticals' },
      { area: 'Misdirection', severity: 'high', description: 'Crashes hard on run action, vulnerable to counters and reverses' },
      { area: 'Check-Down Defense', severity: 'medium', description: 'Linebackers vacate zones on blitz, leaving underneath open' },
    ],
    behavioralSignals: [
      { type: 'audible', description: 'Frequently audibles to blitz when offense shows empty', frequency: 'frequent', situation: 'Empty backfield sets' },
      { type: 'pace-change', description: 'Speeds up tempo after big defensive plays', frequency: 'occasional', situation: 'After sacks or TFLs' },
      { type: 'timeout', description: 'Calls timeout before critical 3rd downs in 2nd half', frequency: 'rare', situation: 'Late-game 3rd and long' },
    ],
    killSheet: [
      { id: 'ks-1', playName: 'HB Screen', formation: 'Shotgun Trips', confidenceScore: 92, successRate: 78, description: 'Exploits aggressive pass rush. Let DL get upfield, dump to HB behind pulling linemen.' },
      { id: 'ks-2', playName: 'PA Crossers', formation: 'Singleback Ace', confidenceScore: 87, successRate: 72, description: 'Play action freezes LBs, crossing routes beat man coverage underneath.' },
      { id: 'ks-3', playName: 'Four Verticals', formation: 'Shotgun Empty', confidenceScore: 81, successRate: 65, description: 'Attack single-high safety with 4 vertical threats. Read safety rotation post-snap.' },
      { id: 'ks-4', playName: 'Counter Run', formation: 'I-Form Tight', confidenceScore: 78, successRate: 68, description: 'Misdirection exploits over-aggressive LB pursuit. Pull guard seals the edge.' },
      { id: 'ks-5', playName: 'Wheel Route', formation: 'Shotgun Bunch', confidenceScore: 74, successRate: 61, description: 'RB wheel vs blitzing LB creates easy mismatch down the sideline.' },
    ],
    encounters: [
      { id: 'enc-1', date: '2026-03-20', result: 'win', score: '28-14', notes: 'Dominated with screens and counters after adjusting in 2nd quarter', mode: 'ranked' },
      { id: 'enc-2', date: '2026-03-15', result: 'win', score: '24-21', notes: 'Close game, won on late drive using PA Crossers', mode: 'ranked' },
      { id: 'enc-3', date: '2026-03-10', result: 'loss', score: '14-28', notes: 'Got sacked 7 times, did not adjust to blitz quick enough', mode: 'tournament' },
      { id: 'enc-4', date: '2026-03-05', result: 'win', score: '35-17', notes: 'Screens were automatic. They could not stop HB Screen all game', mode: 'ranked' },
      { id: 'enc-5', date: '2026-02-28', result: 'loss', score: '10-24', notes: 'Ran too many deep routes into blitz, need more quick game', mode: 'ranked' },
      { id: 'enc-6', date: '2026-02-22', result: 'win', score: '21-17', notes: 'Mixed run and pass well, counters worked great', mode: 'ranked' },
      { id: 'enc-7', date: '2026-02-18', result: 'loss', score: '7-31', notes: 'First time facing this opponent, completely unprepared for blitz', mode: 'ranked' },
      { id: 'enc-8', date: '2026-02-15', result: 'win', score: '17-14', notes: 'Grinded it out with run game after scouting report adjustments', mode: 'ranked' },
    ],
  },
  {
    id: 'opp-2',
    gamertag: 'AirRaidKing',
    archetype: 'Air Raid',
    encounterCount: 5,
    lastSeen: '5d ago',
    winRate: 40,
    isRival: true,
    record: { wins: 2, losses: 3 },
    blitzFrequency: 25,
    scoutedAt: '2026-01-20',
    formationFrequencies: [
      { formation: 'Shotgun Spread', percentage: 40 },
      { formation: 'Shotgun Empty', percentage: 30 },
      { formation: 'Shotgun Trips', percentage: 20 },
      { formation: 'Pistol', percentage: 10 },
    ],
    archetypeDetail: {
      description: 'Pass-first mentality with spread formations. Uses mesh concepts, deep posts, and RPOs to stretch the field horizontally and vertically.',
      strengths: ['Quick release reads', 'Explosive passing plays', 'Excellent route combinations'],
      weaknesses: ['Predictable in run game', 'Struggles under pressure', 'Abandons run too early'],
    },
    tendencies: [
      { label: 'Short Pass', percentage: 55, category: 'offense' },
      { label: 'Deep Pass', percentage: 35, category: 'offense' },
      { label: 'RPO', percentage: 40, category: 'offense' },
      { label: 'Cover 3', percentage: 50, category: 'defense' },
      { label: 'Cover 4', percentage: 30, category: 'defense' },
      { label: 'Blitz', percentage: 25, category: 'defense' },
    ],
    playFrequencies: [
      { playName: 'Mesh Concept', count: 22, successRate: 68 },
      { playName: 'Four Verticals', count: 16, successRate: 55 },
      { playName: 'Stick Concept', count: 14, successRate: 62 },
      { playName: 'PA Boot Over', count: 11, successRate: 50 },
      { playName: 'Y-Trail', count: 9, successRate: 58 },
    ],
    weaknesses: [
      { area: 'Run Defense', severity: 'critical', description: 'Light boxes in nickel/dime make them vulnerable to power runs', exploitPlay: 'Inside Zone' },
      { area: 'Pressure Handling', severity: 'high', description: 'QB panics under consistent pressure, throws off-platform', exploitPlay: 'Mid Blitz' },
      { area: 'Clock Management', severity: 'medium', description: 'Pass-heavy approach leads to fast possessions and clock issues' },
    ],
    behavioralSignals: [
      { type: 'hot-route', description: 'Adjusts WR routes pre-snap when seeing press coverage', frequency: 'frequent', situation: 'Press man alignments' },
      { type: 'formation-shift', description: 'Shifts to empty set on 3rd and medium', frequency: 'occasional', situation: '3rd and 4-7' },
    ],
    killSheet: [
      { id: 'ks-6', playName: 'Inside Zone', formation: 'I-Form Pro', confidenceScore: 90, successRate: 75, description: 'Attack light boxes with downhill running. They cannot stop the run from nickel.' },
      { id: 'ks-7', playName: 'Mid Blitz', formation: 'Nickel 3-3-5', confidenceScore: 85, successRate: 70, description: 'Bring heat up the middle. QB crumbles under interior pressure.' },
      { id: 'ks-8', playName: 'Power O', formation: 'I-Form Tight', confidenceScore: 82, successRate: 68, description: 'Physical run game wears down their undersized front.' },
      { id: 'ks-9', playName: 'Cover 2 Man', formation: 'Dollar', confidenceScore: 76, successRate: 60, description: 'Bracket their top WR, force underneath throws, rally to ball.' },
      { id: 'ks-10', playName: 'QB Contain', formation: '4-3 Over', confidenceScore: 72, successRate: 58, description: 'DEs set the edge, force QB to step up into interior pressure.' },
    ],
    encounters: [
      { id: 'enc-9', date: '2026-03-17', result: 'loss', score: '21-35', notes: 'Could not stop mesh concept, need better zone drops', mode: 'ranked' },
      { id: 'enc-10', date: '2026-03-08', result: 'win', score: '28-21', notes: 'Ran the ball 30 times, controlled clock and won', mode: 'ranked' },
      { id: 'enc-11', date: '2026-02-25', result: 'loss', score: '17-31', notes: 'Threw too much trying to keep up with their passing attack', mode: 'tournament' },
      { id: 'enc-12', date: '2026-02-12', result: 'loss', score: '14-24', notes: 'Did not commit to run game early enough', mode: 'ranked' },
      { id: 'enc-13', date: '2026-01-20', result: 'win', score: '24-17', notes: 'Blitzed heavily and it worked. QB was rattled all game', mode: 'ranked' },
    ],
  },
  {
    id: 'opp-3',
    gamertag: 'GridironGhost',
    archetype: 'West Coast',
    encounterCount: 3,
    lastSeen: '1w ago',
    winRate: 67,
    isRival: true,
    record: { wins: 2, losses: 1 },
    blitzFrequency: 35,
    scoutedAt: '2026-02-01',
    formationFrequencies: [
      { formation: 'Singleback Ace', percentage: 30 },
      { formation: 'Shotgun Doubles', percentage: 25 },
      { formation: 'I-Form Pro', percentage: 25 },
      { formation: 'Pistol Trips', percentage: 20 },
    ],
    archetypeDetail: {
      description: 'Methodical short-to-intermediate passing with a balanced run game. Uses timing routes and high-percentage throws to move chains.',
      strengths: ['Consistent chain-moving', 'Balanced play calling', 'Excellent 3rd down conversion'],
      weaknesses: ['Lacks explosive plays', 'Predictable route depth', 'Conservative in red zone'],
    },
    tendencies: [
      { label: 'Short Pass', percentage: 48, category: 'offense' },
      { label: 'Mid Pass', percentage: 32, category: 'offense' },
      { label: 'Run', percentage: 38, category: 'offense' },
      { label: 'Cover 3', percentage: 42, category: 'defense' },
      { label: 'Cover 2', percentage: 35, category: 'defense' },
      { label: 'Man Press', percentage: 28, category: 'defense' },
    ],
    playFrequencies: [
      { playName: 'Slant Flat', count: 18, successRate: 65 },
      { playName: 'Curl Flat', count: 15, successRate: 60 },
      { playName: 'Inside Zone', count: 14, successRate: 55 },
      { playName: 'PA Crossers', count: 10, successRate: 70 },
      { playName: 'Out Route', count: 8, successRate: 58 },
    ],
    weaknesses: [
      { area: 'Red Zone', severity: 'high', description: 'Settles for field goals too often inside the 20', exploitPlay: 'Cover 2 Man' },
      { area: 'Deep Ball', severity: 'medium', description: 'Rarely takes deep shots, can play tighter coverage underneath' },
      { area: 'Tempo', severity: 'medium', description: 'Struggles when forced to play fast, prefers methodical pace' },
    ],
    behavioralSignals: [
      { type: 'pace-change', description: 'Slows down tempo dramatically in the 4th quarter with a lead', frequency: 'frequent', situation: 'Leading in 4th quarter' },
      { type: 'audible', description: 'Checks to run when seeing single-high safety', frequency: 'occasional', situation: 'Single-high looks' },
    ],
    killSheet: [
      { id: 'ks-11', playName: 'Press Man Blitz', formation: 'Nickel 3-3-5', confidenceScore: 88, successRate: 72, description: 'Jam receivers at the line to disrupt timing. Short routes become contested throws.' },
      { id: 'ks-12', playName: 'Cover 4 Drop', formation: '4-3 Under', confidenceScore: 82, successRate: 66, description: 'Take away intermediate routes and force them deep where they are uncomfortable.' },
      { id: 'ks-13', playName: 'No-Huddle Offense', formation: 'Shotgun Spread', confidenceScore: 79, successRate: 64, description: 'Push tempo to prevent their methodical play calling.' },
      { id: 'ks-14', playName: 'Cover 2 Sink', formation: 'Nickel Normal', confidenceScore: 75, successRate: 60, description: 'Sink underneath zones to take away slants and curls.' },
      { id: 'ks-15', playName: 'Aggressive Red Zone D', formation: 'Goal Line', confidenceScore: 71, successRate: 58, description: 'Blitz in red zone to force hurried throws and field goals.' },
    ],
    encounters: [
      { id: 'enc-14', date: '2026-03-15', result: 'win', score: '21-13', notes: 'Press man shut down their short game completely', mode: 'ranked' },
      { id: 'enc-15', date: '2026-03-01', result: 'loss', score: '14-17', notes: 'Could not stop 3rd down conversions. Death by a thousand cuts.', mode: 'ranked' },
      { id: 'enc-16', date: '2026-02-01', result: 'win', score: '28-10', notes: 'Pushed tempo and they could not keep up', mode: 'tournament' },
    ],
  },
  {
    id: 'opp-4',
    gamertag: 'BlitzMaster99',
    archetype: 'Blitz Heavy',
    encounterCount: 4,
    lastSeen: '3d ago',
    winRate: 75,
    isRival: true,
    record: { wins: 3, losses: 1 },
    blitzFrequency: 80,
    scoutedAt: '2026-01-10',
    formationFrequencies: [
      { formation: 'Nickel 3-3-5', percentage: 40 },
      { formation: 'Big Nickel', percentage: 25 },
      { formation: 'Dollar', percentage: 20 },
      { formation: '3-4 Odd', percentage: 15 },
    ],
    archetypeDetail: {
      description: 'Maximum pressure defense with exotic blitz packages. Sends 5-7 rushers on most plays, relying on confusion and speed to get to the QB.',
      strengths: ['Overwhelming pressure', 'Forces turnovers', 'Creates negative plays'],
      weaknesses: ['Leaves receivers in single coverage', 'Vulnerable to hot routes', 'Burns when blitz is picked up'],
    },
    tendencies: [
      { label: 'Zone Blitz', percentage: 55, category: 'defense' },
      { label: 'Man Blitz', percentage: 65, category: 'defense' },
      { label: 'DB Blitz', percentage: 40, category: 'defense' },
      { label: 'Run', percentage: 45, category: 'offense' },
      { label: 'Play Action', percentage: 35, category: 'offense' },
      { label: 'Short Pass', percentage: 30, category: 'offense' },
    ],
    playFrequencies: [
      { playName: 'Cover 0 Blitz', count: 28, successRate: 55 },
      { playName: 'DB Fire 2', count: 20, successRate: 50 },
      { playName: 'Overload Blitz', count: 16, successRate: 48 },
      { playName: 'Inside Zone', count: 12, successRate: 60 },
      { playName: 'PA Shot', count: 8, successRate: 65 },
    ],
    weaknesses: [
      { area: 'Hot Routes', severity: 'critical', description: 'Cannot cover quick slants and drags when sending 6+', exploitPlay: 'Quick Slant' },
      { area: 'Screen Game', severity: 'critical', description: 'Over-pursuit makes screens devastating', exploitPlay: 'WR Screen' },
      { area: 'Play Action', severity: 'high', description: 'LBs bite hard on run fakes when not blitzing' },
    ],
    behavioralSignals: [
      { type: 'formation-shift', description: 'Shows blitz pre-snap then drops into coverage', frequency: 'occasional', situation: '3rd and long' },
      { type: 'timeout', description: 'Uses timeouts aggressively to set up blitz packages', frequency: 'frequent', situation: 'Opponent red zone trips' },
      { type: 'pace-change', description: 'Hurries to the line on offense after defensive stops', frequency: 'occasional', situation: 'After turnovers' },
    ],
    killSheet: [
      { id: 'ks-16', playName: 'Quick Slant', formation: 'Shotgun Doubles', confidenceScore: 94, successRate: 80, description: 'Hot route into blitz. Ball out in under 2 seconds beats any pressure.' },
      { id: 'ks-17', playName: 'WR Screen', formation: 'Shotgun Trips', confidenceScore: 90, successRate: 76, description: 'Let rushers fly by, dump to WR behind blocking. Huge YAC potential.' },
      { id: 'ks-18', playName: 'Draw Play', formation: 'Shotgun Spread', confidenceScore: 84, successRate: 68, description: 'Suck LBs upfield on pass rush, hand off into vacated space.' },
      { id: 'ks-19', playName: 'Max Protect Deep', formation: 'Singleback Ace', confidenceScore: 78, successRate: 62, description: 'Block 7, send 2 deep. Single coverage means big play opportunity.' },
      { id: 'ks-20', playName: 'TE Seam', formation: 'Shotgun Y-Trips', confidenceScore: 73, successRate: 58, description: 'TE up the seam exploits vacated middle when LBs blitz.' },
    ],
    encounters: [
      { id: 'enc-17', date: '2026-03-19', result: 'win', score: '35-10', notes: 'Quick game destroyed their blitz. Slants and screens all day', mode: 'tournament' },
      { id: 'enc-18', date: '2026-03-06', result: 'win', score: '28-21', notes: 'Adjusted at half to more hot routes, turned it around', mode: 'ranked' },
      { id: 'enc-19', date: '2026-02-20', result: 'loss', score: '7-24', notes: 'Held ball too long against pressure. Need quicker reads', mode: 'ranked' },
      { id: 'enc-20', date: '2026-01-10', result: 'win', score: '31-14', notes: 'Draw plays and screens were unstoppable', mode: 'ranked' },
    ],
  },
  {
    id: 'opp-5',
    gamertag: 'PocketGeneral',
    archetype: 'Pocket Passer',
    encounterCount: 2,
    lastSeen: '2w ago',
    winRate: 50,
    isRival: false,
    record: { wins: 1, losses: 1 },
    blitzFrequency: 30,
    formationFrequencies: [
      { formation: 'Shotgun Doubles', percentage: 35 },
      { formation: 'Singleback Ace', percentage: 30 },
      { formation: 'I-Form Pro', percentage: 20 },
      { formation: 'Shotgun Trips', percentage: 15 },
    ],
    archetypeDetail: {
      description: 'Patient passer who reads defenses pre-snap and works through progressions. Rarely scrambles but makes accurate throws from the pocket.',
      strengths: ['Excellent pre-snap reads', 'Accurate intermediate throws', 'Rarely turns the ball over'],
      weaknesses: ['Immobile in pocket', 'Struggles with exotic pressure', 'Slow to adjust mid-game'],
    },
    tendencies: [
      { label: 'Mid Pass', percentage: 45, category: 'offense' },
      { label: 'Deep Pass', percentage: 28, category: 'offense' },
      { label: 'Check Down', percentage: 35, category: 'offense' },
      { label: 'Cover 2', percentage: 40, category: 'defense' },
      { label: 'Tampa 2', percentage: 30, category: 'defense' },
      { label: 'Zone Drop', percentage: 35, category: 'defense' },
    ],
    playFrequencies: [
      { playName: 'Curl Flat', count: 14, successRate: 62 },
      { playName: 'PA Deep Post', count: 10, successRate: 58 },
      { playName: 'Smash Concept', count: 9, successRate: 55 },
      { playName: 'Inside Zone', count: 8, successRate: 50 },
    ],
    weaknesses: [
      { area: 'Mobility', severity: 'high', description: 'Cannot escape collapsing pocket, sack rate spikes with interior rush' },
      { area: 'Mid-Game Adjustment', severity: 'medium', description: 'Slow to change gameplan when initial approach is not working' },
    ],
    behavioralSignals: [
      { type: 'audible', description: 'Frequently audibles based on defensive alignment', frequency: 'frequent', situation: 'Most pre-snap situations' },
    ],
    killSheet: [
      { id: 'ks-21', playName: 'Interior Blitz', formation: 'Nickel 3-3-5', confidenceScore: 86, successRate: 70, description: 'A-gap pressure collapses pocket. Immobile QB has nowhere to go.' },
      { id: 'ks-22', playName: 'DT Twist', formation: '4-3 Under', confidenceScore: 80, successRate: 65, description: 'Interior games create free rushers up the middle.' },
      { id: 'ks-23', playName: 'Sim Pressure', formation: 'Nickel Normal', confidenceScore: 77, successRate: 62, description: 'Show blitz, drop into coverage. Confuse pre-snap reads.' },
      { id: 'ks-24', playName: 'Zone Fire', formation: '3-4 Odd', confidenceScore: 73, successRate: 58, description: 'Zone blitz disguise. Drop DE, send LB from unexpected angle.' },
      { id: 'ks-25', playName: 'Cover 6', formation: '4-3 Over', confidenceScore: 70, successRate: 55, description: 'Mix coverages to disrupt progression reads.' },
    ],
    encounters: [
      { id: 'enc-21', date: '2026-03-08', result: 'win', score: '24-17', notes: 'Interior pressure worked. 4 sacks, 2 forced fumbles', mode: 'ranked' },
      { id: 'enc-22', date: '2026-02-15', result: 'loss', score: '14-21', notes: 'Played too much zone, they picked us apart with reads', mode: 'ranked' },
    ],
  },
  {
    id: 'opp-6',
    gamertag: 'RunItBack_44',
    archetype: 'Run First',
    encounterCount: 1,
    lastSeen: '3w ago',
    winRate: 0,
    isRival: false,
    record: { wins: 0, losses: 1 },
    blitzFrequency: 18,
    scoutedAt: '2026-03-01',
    formationFrequencies: [
      { formation: 'I-Form Tight', percentage: 35 },
      { formation: 'Singleback Deuce', percentage: 30 },
      { formation: 'Goal Line', percentage: 20 },
      { formation: 'Pistol Strong', percentage: 15 },
    ],
    archetypeDetail: {
      description: 'Ground-and-pound offense that controls the clock with heavy personnel. Uses 2-TE and fullback sets to establish the run and wear down defenses.',
      strengths: ['Clock control', 'Physical at the point of attack', 'Demoralizing late-game run game'],
      weaknesses: ['Limited passing attack', 'Falls behind easily', 'Predictable formation tendencies'],
    },
    tendencies: [
      { label: 'Inside Run', percentage: 55, category: 'offense' },
      { label: 'Outside Run', percentage: 30, category: 'offense' },
      { label: 'Play Action', percentage: 25, category: 'offense' },
      { label: 'Cover 3', percentage: 45, category: 'defense' },
      { label: 'Cover 1', percentage: 30, category: 'defense' },
      { label: 'Run Commit', percentage: 40, category: 'defense' },
    ],
    playFrequencies: [
      { playName: 'Inside Zone', count: 20, successRate: 62 },
      { playName: 'Power O', count: 16, successRate: 58 },
      { playName: 'Counter', count: 12, successRate: 55 },
      { playName: 'PA Boot', count: 8, successRate: 50 },
    ],
    weaknesses: [
      { area: 'Passing Game', severity: 'critical', description: 'Very limited passing concepts, can be shut down with stacked boxes', exploitPlay: 'Cover 1 Robber' },
      { area: 'Coming From Behind', severity: 'high', description: 'Panics when forced to throw, turnover-prone', exploitPlay: 'Press Man Blitz' },
      { area: 'Formation Tells', severity: 'high', description: 'Heavy personnel = run, light personnel = pass. Very predictable.', exploitPlay: 'Run Commit' },
    ],
    behavioralSignals: [
      { type: 'pace-change', description: 'Milks play clock to absolute limit every play', frequency: 'frequent', situation: 'All game situations' },
      { type: 'formation-shift', description: 'Motions TE to identify coverage before the snap', frequency: 'occasional', situation: 'Early downs' },
    ],
    killSheet: [
      { id: 'ks-26', playName: 'Cover 1 Robber', formation: '4-3 Over', confidenceScore: 91, successRate: 78, description: 'Stack the box with 8. Force them to beat you throwing, which they cannot.' },
      { id: 'ks-27', playName: 'Pinch DL', formation: '3-4 Bear', confidenceScore: 86, successRate: 72, description: 'Pinch DL to stuff inside runs. Force bounces to the outside.' },
      { id: 'ks-28', playName: 'Score Early', formation: 'Shotgun Spread', confidenceScore: 82, successRate: 68, description: 'Get ahead early to take them out of their gameplan. Force passing.' },
      { id: 'ks-29', playName: 'Contain DEs', formation: '4-3 Under', confidenceScore: 78, successRate: 64, description: 'Set the edge to prevent outside runs. Funnel inside for LB tackles.' },
      { id: 'ks-30', playName: 'Press Man', formation: 'Nickel Normal', confidenceScore: 72, successRate: 58, description: 'When they do pass, press coverage disrupts their limited route tree.' },
    ],
    encounters: [
      { id: 'enc-23', date: '2026-03-01', result: 'loss', score: '10-28', notes: 'Could not stop the run. They had 250+ rushing yards', mode: 'ranked' },
    ],
  },
];

export function useOpponents() {
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<OpponentFilter>('all');
  const [sort, setSort] = useState<OpponentSort>('lastSeen');

  const filtered = useMemo(() => {
    let result = [...mockOpponents];

    // Search
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter((o) => o.gamertag.toLowerCase().includes(q));
    }

    // Filter
    switch (filter) {
      case 'rivals':
        result = result.filter((o) => o.isRival);
        break;
      case 'recent':
        result = result.filter((o) => o.encounterCount > 0);
        result.sort((a, b) => {
          const parseRecency = (s: string) => {
            if (s.includes('d')) return parseInt(s);
            if (s.includes('w')) return parseInt(s) * 7;
            return 999;
          };
          return parseRecency(a.lastSeen) - parseRecency(b.lastSeen);
        });
        break;
      case 'scouted':
        result = result.filter((o) => !!o.scoutedAt);
        break;
    }

    // Sort
    switch (sort) {
      case 'lastSeen': {
        const parseRecency = (s: string) => {
          if (s.includes('d')) return parseInt(s);
          if (s.includes('w')) return parseInt(s) * 7;
          return 999;
        };
        result.sort((a, b) => parseRecency(a.lastSeen) - parseRecency(b.lastSeen));
        break;
      }
      case 'encounters':
        result.sort((a, b) => b.encounterCount - a.encounterCount);
        break;
      case 'winRate':
        result.sort((a, b) => b.winRate - a.winRate);
        break;
    }

    return result;
  }, [search, filter, sort]);

  const getOpponentById = (id: string): Opponent | undefined => {
    return mockOpponents.find((o) => o.id === id);
  };

  return {
    opponents: filtered,
    search,
    setSearch,
    filter,
    setFilter,
    sort,
    setSort,
    getOpponentById,
  };
}
