#include "clickableqwidget.hpp"

ClickableQWidget::ClickableQWidget(QWidget *parent)
    : QWidget{parent} {}

void ClickableQWidget::mousePressEvent(QMouseEvent *) {
    emit clicked();
}
