#ifndef CLICKABLEQWIDGET_HPP
#define CLICKABLEQWIDGET_HPP

#include <QWidget>

class ClickableQWidget : public QWidget {
    Q_OBJECT
public:
    explicit ClickableQWidget(QWidget *parent = nullptr);

protected:
    void mousePressEvent(QMouseEvent *) override;

signals:
    void clicked();
};

#endif // CLICKABLEQWIDGET_HPP
