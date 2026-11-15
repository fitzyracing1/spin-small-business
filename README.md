# spin-small-business

[![Sponsor](https://img.shields.io/badge/Sponsor-fitzyracing1-ea4aaa?logo=githubsponsors)](https://github.com/sponsors/fitzyracing1)
[![test](https://github.com/fitzyracing1/spin-small-business/actions/workflows/test.yml/badge.svg)](https://github.com/fitzyracing1/spin-small-business/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Summarize a bookkeeping CSV by category and estimate quarterly tax from a rate you supply. Same input, same answer, no API, no cost, works offline.

You supply the tax rate. It is a math helper, not tax advice. It does not apply deductions, credits, annualization, or filing rules.

```sh
python small_business.py summarize testdata/books.csv
python small_business.py tax testdata/books.csv --rate 25%
```

CSV columns: `date,description,category,amount,type`. Dates are `YYYY-MM-DD`. Amounts are unsigned; `type` is `income` or `expense`. Totals use `Decimal` math, rounded half-up to cents.

The tax helper prints two views: each calendar quarter's net times your rate (a negative quarter estimates 0 for that quarter), and four equal installments of (yearly net * rate), where losses offset gains across the year.

## Run it

It's plain Python 3 with no packages to install, so it runs anywhere Python does.

```sh
gh repo clone fitzyracing1/spin-small-business
cd spin-small-business
python small_business.py
python -m pytest -q
```

### Windows (PowerShell)
```powershell
winget install Python.Python.3.12 GitHub.cli
gh auth login
gh repo clone fitzyracing1/spin-small-business; cd spin-small-business; py small_business.py
```

### Mac
```sh
brew install python gh && gh auth login
gh repo clone fitzyracing1/spin-small-business && cd spin-small-business && python3 small_business.py
```

### Linux
```sh
sudo apt install -y python3 gh && gh auth login
gh repo clone fitzyracing1/spin-small-business && cd spin-small-business && python3 small_business.py
```

### Termux (Android)
```sh
pkg install -y python git gh && gh auth login
gh repo clone fitzyracing1/spin-small-business ~/spin-small-business && cd ~/spin-small-business && python small_business.py
```

## Support this project

spin-small-business is free and MIT licensed. If it saves you time, please [sponsor me on GitHub](https://github.com/sponsors/fitzyracing1). It keeps the tools coming.

| Plan | Price | What you get |
| --- | --- | --- |
| Free | $0 | Everything in this repo, forever |
| Pro | $49/month | Priority issues and help adding your own tools |
| Team | $199/month | Custom tools built for your team, plus Pro |

Plans are paid through [GitHub Sponsors](https://github.com/sponsors/fitzyracing1). You can also star the repo, share it, or open an issue with a tool idea.

## Author

Built by Joshua Almeida ([@fitzyracing1](https://x.com/fitzyracing1), [fitzyracing1.com](https://fitzyracing1.com), [GitHub](https://github.com/fitzyracing1)).

## License

[MIT](LICENSE) © 2026 Joshua Almeida
