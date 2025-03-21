#ifndef CLICKABLEQWIDGET_HPP
#define CLICKABLEQWIDGET_HPP

#include <QWidget>

class ClickableQWidget : public QWidget {
    Q_OBJECT
public:
    explicit ClickableQWidget(QWidget *parent = nullptr);
    void set_clickable(bool on);
    bool is_clickable();

protected:
    void mouseMoveEvent(QMouseEvent *) override;
    void mousePressEvent(QMouseEvent *) override;

private:
    bool clickable;

signals:
    void clicked();
};

#endif // CLICKABLEQWIDGET_HPP
