#ifndef PROCESSPAGE_HPP
#define PROCESSPAGE_HPP

#include <QTableWidget>
#include <QWidget>

namespace Ui {
class ProcessPage;
}

class ProcessPage : public QWidget {
    Q_OBJECT

public:
    explicit ProcessPage(QWidget *parent = nullptr);
    ~ProcessPage();

    void set_preview(QPixmap image);
    void clear_preview();
    void fill_metadata(QStringList metadata);
    void set_temperature_type(QString type);

private slots:
    void on_pb_refresh_clicked();
    void on_pb_meta_clicked();
    void on_pb_go_clicked();

signals:
    void preview(uint w, uint h);
    void require_metadata();
    void indices(QStringList);

private:
    Ui::ProcessPage *ui;
    QTableWidget    *tb;
    QString          temperature_type;
};

#endif // PROCESSPAGE_HPP
