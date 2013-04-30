library(ggplot2)
library(plyr)
rm(list=ls())
x <- read.csv("~/Dropbox/fun/baseball/numbers/combined_data.csv", stringsAsFactors=FALSE)
sum(duplicated(x))
x <- x[!duplicated(x), ]
x$number <- as.numeric(x$number)
x <- subset(x, number > 0 & batting_average > 0)
x$plate_appearances <- as.numeric(x$plate_appearances)
x$batting_average <- as.numeric(x$batting_average)
x$is_pitcher <- factor(x$is_pitcher)

x <- subset(x, plate_appearances >= 500)
x <- x[order(-x$batting_average), ]

ggplot(x, aes(x=factor(number), y=batting_average)) +
  geom_point(alpha=.5, aes(color=is_pitcher)) +
  scale_x_discrete("Jersey Number") +
  scale_y_continuous("Batting Average") +
  coord_flip()

numbers <- ddply(subset(x, is_pitcher==0), .(number), 
                 summarize,
                 ba=mean(batting_average),
                 pa=mean(plate_appearances),
                 score=sum(batting_average * plate_appearances / sum(plate_appearances)),
                 players=length(batting_average))

numbers <- subset(numbers, players > 4)
numbers$num <- factor(numbers$number)

ggplot(numbers, aes(x=number, y=score)) +
  geom_text(aes(label=number)) +
  ggtitle('Weighted Batting Average by Player Number\nMinimum 500 at bats, 5 players per number') +
  scale_x_continuous("Jersey Number") +
  scale_y_continuous("Batting Average Score")


## weighted average batting average
sum(numbers$ba * numbers$pa / sum(numbers$pa))
qplot(plate_appearances, batting_average, data=x, color=is_pitcher)