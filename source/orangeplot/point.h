#ifndef POINT_H
#define POINT_H

#include <QtGui/QGraphicsItem>


struct DataPoint
{
  double x;
  double y;
};

struct PointData
{
    PointData(int size, int symbol, const QColor& color, int state, bool transparent) : size(size), symbol(symbol), color(color), state(state), transparent(transparent) {}
    int size;
    int symbol;
    QColor color;
    int state;
    bool transparent;
};

uint qHash(const PointData& data);
bool operator==(const PointData& one, const PointData& other);

class Point : public QGraphicsItem
{

public:
    enum DisplayMode
    {
        DisplayPixmap,
        DisplayPath
    };
    
  /**
   * @brief Point symbol
   * 
   * The symbols list here matches the one from QwtPlotCurve. 
   **/
  enum Symbol {
    NoSymbol = -1,
    Ellipse = 0,
    Rect = 1,
    Diamond = 2,
    Triangle = 3,
    DTriangle = 4,
    UTriangle = 5,
    LTriangle = 6,
    RTriangle = 7,
    Cross = 8,
    XCross = 9,
    HLine = 10,
    VLine = 11,
    Star1 = 12,
    Star2 = 13,
    Hexagon = 14,
    UserStyle = 1000
  };
  
    enum StateFlag
    {
        Normal = 0x00,
        Marked = 0x01,
        Selected = 0x02
    };
    
    Q_DECLARE_FLAGS(State, StateFlag)
  
    enum 
    {
        Type = UserType + 1
    };
    
    virtual int type() const
    {
        return Type;
    }
    
    explicit Point(QGraphicsItem* parent = 0, QGraphicsScene* scene = 0);
    Point(int symbol, QColor color, int size, QGraphicsItem* parent = 0);
    virtual ~Point();
    
    virtual void paint(QPainter* painter, const QStyleOptionGraphicsItem* option, QWidget* widget = 0);
    virtual QRectF boundingRect() const;
    
    void set_symbol(int symbol);
    int symbol() const;
    
    void set_color(const QColor& color);
    QColor color() const;
    
    void set_size(int size);
    int size() const;
    
    void set_display_mode(DisplayMode mode);
    DisplayMode display_mode() const;
    
    void set_state(State state);
    State state() const;
    void set_state_flag(StateFlag flag, bool on);
    bool state_flag(StateFlag flag) const;
    
    void set_selected(bool selected);
    bool is_selected() const;

    void set_marked(bool marked);
    bool is_marked() const;

    bool is_transparent();
    void set_transparent(bool transparent);
    
    DataPoint coordinates() const;
    void set_coordinates(const DataPoint& data_point);
    
    void set_label(const QString& label);
    QString label() const;
    
    /**
    * Creates a path from a symbol and a size
    *
    * @param symbol the point symbol to use
    * @param size the size of the resulting path
    * @return a path that can be used in a QGraphicsPathItem or in QPainter::drawPath()
    **/
    static QPainterPath path_for_symbol(int symbol, int size);
    
    static QPixmap pixmap_for_symbol(int symbol, QColor color, int size);
    static QRectF rect_for_size(double size);
    
    static void clear_cache();

    static QHash<PointData, QPixmap> pixmap_cache;

private:
    static QPainterPath trianglePath(double d, double rot);
    static QPainterPath crossPath(double d, double rot);
    static QPainterPath hexPath(double d, bool star);

    int m_symbol;
    QColor m_color;
    int m_size;
    DisplayMode m_display_mode;
    State m_state;
    bool m_transparent;
    
    DataPoint m_coordinates;
    QString m_label;
};

struct PointPosUpdater
{
  PointPosUpdater(QTransform t) : t(t) {}
  void operator()(Point* point)
  {
    point->setPos(t.map(QPointF(point->coordinates().x, point->coordinates().y)));
  }
  
private:
    QTransform t;
};

#endif // POINT_H
