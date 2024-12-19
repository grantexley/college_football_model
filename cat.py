#!/usr/bin/env python3

import sys


def main():
    result = ""
    for file in ["cfp_data_2016", "cfp_data_2017", "cfp_data_2018", "cfp_data_2019", "cfp_data_2020", "cfp_data_2021", "cfp_data_2022", "cfp_data_2023", "cfp_data_2024"]:
        
        with open(file, "r") as f:
            result += f.read()

    with open("all_data.csv", "w") as fc:
        f.write(result)

if __name__ == '__main__':
    main()