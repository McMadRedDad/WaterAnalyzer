#ifndef MAINWINDOW_HPP
#define MAINWINDOW_HPP

#include <QMainWindow>
#include <QMessageBox>
#include <QTcpSocket>
#include <QTimer>
#include "clickableqwidget.hpp"

QT_BEGIN_NAMESPACE
namespace Ui {
class MainWindow;
}
QT_END_NAMESPACE

struct STATE {
    enum CurrPage { BAD = -1, IMPORT, SELECTION, RESULT } page;
    QList<ClickableQWidget *> pages; // same order as CurrPage
};

class MainWindow : public QMainWindow {
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private slots:
    void on_pushButton_back_clicked();
    void on_pushButton_showLog_clicked();

private:
    Ui::MainWindow *ui;
    STATE           state;
    QTimer          timer_status;
    QTcpSocket     *json_sock;
    QTcpSocket     *http_sock;
    QHostAddress    backend_host;
    quint16         json_port;
    quint16         http_port;

    void set_status_message(bool good, QString message, short msec);
    void clear_status();
    void append_log(QString line);
    void init_connection(QAbstractSocket *socket, QHostAddress address, quint16 port);
    void socket_error();
    void socket_connection();
    void socket_read();

    void import_clicked();
};
#endif // MAINWINDOW_HPP
