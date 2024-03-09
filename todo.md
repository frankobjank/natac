Current todo:
    add dice check after move_robber() and steal() (and all dev_card_modes)



Ideas:
things to add to info_box:
    title of mode at top
    put player selection for stealing at mode "steal"
    put card selection for discarding at mode "discard_cards"

    have general layout of mode title at the top of info_box and mode details below
    can be wrapped in render_info_box function that includes all the modes

to add to hand UI:
    when selecting something to trade away or discard, show -> minus cards
        when gaining a card, show -> add cards

trade interface UI:
    set up vertically instead of horizantally
    use same infrastructure as discard cards. offer side same as discard, receive side is plus
    be able to move offer/receive focus .. with mouse or arrow keys?
    draw box around selection




Known bugs:
Bug 1 - submit button not working --- !!!
Bug 2 - end turn button hover sticking
Bug 3 - When another player enters game after game start, skips some players' turns. This probably won't be an issue in a real game since all players must enter before starting the game.


