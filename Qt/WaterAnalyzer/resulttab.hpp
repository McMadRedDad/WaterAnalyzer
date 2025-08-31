#ifndef RESULTTAB_HPP
#define RESULTTAB_HPP

#include <QWidget>

namespace Ui {
class ResultTab;
}

class ResultTab : public QWidget
{
    Q_OBJECT

public:
    explicit ResultTab(QWidget *parent = nullptr);
    ~ResultTab();

private:
    Ui::ResultTab *ui;
};

#endif // RESULTTAB_HPP
