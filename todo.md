tcp - create test file to try it out
make python bindings for nbnet

function to find node/edge 
    find_node(nodes, node)
    find_edge(edges, edge) - see line 787 main.py



Notes from meet w Victor 12/26

next steps:
Encode game state
Dice
Resources
Player hands
Current player turn:
    Dice roll
    Collect resources

use same seed for dice randomization to make testing easier

client 'action' should be defined before it currently is
    currently mouse hover appears over nodes even when move_robber is selected, but only valid inputs should be highlighted with the mouse hover

client - player should have different 'states'/'actions':
    (could make to enum)
    action: dice roll - only highlight dice/ make dice selectable. everything else not highlighted
    action: None

Turn steps

Client:
    roll dice
    play soldier card - move robber and steal card

if (dice == 7){
    return cards check for all players
    move robber
    steal card
}
else{
    distribute resources to all players
}



client requests mode change locally and passes to server
server receives mode request and confirms if it is possible
server returns decision to client:
    if mouse over, return hover
    if mouse click, return action

client requests mode change back by clicking mode

server should validate mode change/ end turn/ dice roll

turn_phases:
start:
    actions:
        roll dice, play soldier
    modes:
        robber
main:
    actions:
        buy or play development card
    modes:
        build
        trading

end = turn over turn to next player and make mode roll_dice

dice_roll mode 
Essentially can split up turns into two phases: dice roll and main phase


to change for rendering client:
    scale text on buttons with resize
    add box around turn buttons to group them
    change dice button to say roll dice and display dice roll separately so they can be displayed as squares
    add log box either in between or below the button boxes


elements requiring multiple players:
    return_cards -> can only continue (to move_robber) once all players have finished returning cards

figure out way to get multiple clients to join server to test out gameplay features like returning cards, stealing, building, trading, playing dev_cards


OVERALL QUESTION: should server send different response to each client? or same one and then processed by client?
    for returning cards, return_card mode should be determined by server. Maybe make a return mode for all clients like self.mode = {"red": "return_cards", "white": None}

    change dice_roll button to not hover while it's not client_player's turn



Sequence of returning cards:
roll 7
global return_cards mode for everyone
send log
server calcs how many each player must return

clients select cards to be returned. change is reflected on clients (i.e. moving them away from the main hand or drawing 3->2 when adding card to selection)
do not allow selection to go above num cards to return
allow client to submit choice when num cards reaches correct number

server receives choice - again check if it's the number they needed to return, then subtract the cards. check if any players are left in cards to return dict (or if any value is > 0 in that dict)
if yes -> do nothing
if no -> change mode to move_robber




server not picking up non current player input even for return_cards
<!-- make arrow even length from resource name -->
<!-- can't go below 0 value on selected_cards -->
<!-- left arrow should undo right arrow -->
<!-- only show selected cards in render if value > 0 -->
server needs to hash selected_cards differently - set up for dict instead of list
<!-- add marker if player still has cards to return -->