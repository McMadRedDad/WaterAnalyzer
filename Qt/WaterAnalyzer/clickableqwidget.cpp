#include "clickableqwidget.hpp"

ClickableQWidget::ClickableQWidget(QWidget *parent)
    : QWidget{parent} {
    set_clickable(true);
}

void ClickableQWidget::set_clickable(bool on) {
    clickable = on;
}

bool ClickableQWidget::is_clickable() {
    return clickable;
}

void ClickableQWidget::mouseMoveEvent(QMouseEvent *) {
    if (clickable) {
        setCursor(Qt::PointingHandCursor);
    }
}

void ClickableQWidget::mousePressEvent(QMouseEvent *) {
    if (clickable) {
        emit clicked();
    }
}
