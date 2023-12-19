import ofscraper.commands.check as check
import ofscraper.commands.manual as manual
import ofscraper.commands.scraper as scraper
import ofscraper.utils.args as args_


def pick():
    args = args_.getargs()
    if args.command == "post_check":
        check.post_checker()
    elif args.command == "msg_check":
        check.message_checker()
    elif args.command == "paid_check":
        check.purchase_checker()
    elif args.command == "story_check":
        check.stories_checker()
    elif args.command == "manual":
        manual.manual_download()
    else:
        scraper.main()