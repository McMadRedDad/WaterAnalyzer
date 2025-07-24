#ifndef MAINWINDOW_HPP
#define MAINWINDOW_HPP

#include "clickableqwidget.hpp"
#include "jsonprotocol.hpp"
#include <QMainWindow>
#include <QMessageBox>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QTimer>

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
  STATE state;
  QHostAddress backend_ip;
  quint16 backend_port;
  QNetworkAccessManager *net_man;
  JsonProtocol proto;

  Ui::MainWindow *ui;
  QTimer timer_status;

  void send_request(QString type, QString endpoint, QJsonObject data);
  void handle_response(QNetworkReply *response);
  void process_get(QByteArray body);
  void process_post(QUrl endpoint, QByteArray body);

  void set_status_message(bool good, QString message, short msec);
  void clear_status();
  void append_log(QString type, QString line);

  void closeEvent(QCloseEvent *e) override;
  void import_clicked();
};
#endif // MAINWINDOW_HPP
